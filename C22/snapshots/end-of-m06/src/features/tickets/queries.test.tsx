import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { expect, test } from 'vitest';
import type { TicketDetail } from '../../api/types';
import { apiError, deferred, installFakeApi, json, ticket } from '../../test/fakeApi';
import { ticketKeys, useAddMessage, useSetStatus } from './queries';

const detail: TicketDetail = { ...ticket(8), body: 'Where is it?', channel: 'email', updated_at: '', messages: [], has_draft: false };

function setup() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  client.setQueryData(ticketKeys.detail(detail.ticket_id), detail);
  const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  return { client, wrapper };
}

test('a status change shows at once, and goes back when the server refuses it', async () => {
  const answer = deferred<Response>();
  installFakeApi(() => answer.promise);
  const { client, wrapper } = setup();
  const { result } = renderHook(() => useSetStatus(detail.ticket_id), { wrapper });
  act(() => result.current.mutate('pending'));
  await waitFor(() => expect(client.getQueryData<TicketDetail>(ticketKeys.detail(detail.ticket_id))?.status).toBe('pending'));
  answer.resolve(apiError(503, 'unavailable', 'The change was not saved.'));
  await waitFor(() => expect(result.current.isError).toBe(true));
  expect(client.getQueryData<TicketDetail>(ticketKeys.detail(detail.ticket_id))?.status).toBe('open');
});

test('a new message marks the ticket and the lists as stale', async () => {
  installFakeApi(() => json(201, { message_id: 1, author: 'agent', body: 'Hi', created_at: '' }));
  const { client, wrapper } = setup();
  const { result } = renderHook(() => useAddMessage(detail.ticket_id), { wrapper });
  await act(() => result.current.mutateAsync('Hi'));
  expect(client.getQueryState(ticketKeys.detail(detail.ticket_id))?.isInvalidated).toBe(true);
});
