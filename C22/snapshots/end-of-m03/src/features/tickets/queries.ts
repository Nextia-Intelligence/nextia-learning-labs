// Server state of the tickets: the cache keys, the queries and the changes (mutations).
import { useInfiniteQuery, useMutation, useQuery, useQueryClient, type InfiniteData } from '@tanstack/react-query';
import { addMessage, getTicket, listTickets, setStatus } from '../../api/tickets';
import type { Status, TicketDetail, TicketFilter, TicketPage } from '../../api/types';

export const PAGE_SIZE = 50;

/** One place for the cache keys: every key of the tickets starts with 'tickets'. */
export const ticketKeys = {
  all: ['tickets'] as const,
  lists: () => [...ticketKeys.all, 'list'] as const,
  list: (filter: TicketFilter) => [...ticketKeys.lists(), filter] as const,
  detail: (id: string) => [...ticketKeys.all, 'detail', id] as const,
};

/** The list, page by page from the server. A new filter is a new key, so it has its own cache entry. */
export function useTicketList(filter: TicketFilter) {
  return useInfiniteQuery({
    queryKey: ticketKeys.list(filter),
    queryFn: ({ pageParam, signal }) => listTickets(filter, PAGE_SIZE, pageParam, signal),
    initialPageParam: null as string | null,
    getNextPageParam: (last: TicketPage) => last.next,
    placeholderData: (previous) => previous, // keep showing the old results while the new ones load
  });
}

export function useTicket(id: string) {
  return useQuery({ queryKey: ticketKeys.detail(id), queryFn: ({ signal }) => getTicket(id, signal) });
}

/** Adds an agent's message. Not optimistic: a message to a customer cannot be taken back. */
export function useAddMessage(id: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: string) => addMessage(id, body),
    onSuccess: () =>
      Promise.all([
        client.invalidateQueries({ queryKey: ticketKeys.detail(id) }),
        client.invalidateQueries({ queryKey: ticketKeys.lists() }),
      ]),
  });
}

type Lists = InfiniteData<TicketPage, string | null>;

/** Changes the status at once on the screen (optimistic), and puts it back if the server says no. */
export function useSetStatus(id: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (status: Status) => setStatus(id, status),
    onMutate: async (status) => {
      await client.cancelQueries({ queryKey: ticketKeys.all });
      const detail = client.getQueryData<TicketDetail>(ticketKeys.detail(id));
      const lists = client.getQueriesData<Lists>({ queryKey: ticketKeys.lists() });
      client.setQueryData<TicketDetail>(ticketKeys.detail(id), (t) => (t ? { ...t, status } : t));
      client.setQueriesData<Lists>({ queryKey: ticketKeys.lists() }, (data) =>
        data && {
          ...data,
          pages: data.pages.map((p) => ({
            ...p,
            items: p.items.map((t) => (t.ticket_id === id ? { ...t, status } : t)),
          })),
        },
      );
      return { detail, lists };
    },
    onError: (_error, _status, saved) => {
      client.setQueryData(ticketKeys.detail(id), saved?.detail);
      for (const [key, data] of saved?.lists ?? []) client.setQueryData(key, data);
    },
    onSettled: () => client.invalidateQueries({ queryKey: ticketKeys.all }),
  });
}
