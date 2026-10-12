import { useState } from 'react';
import type { TicketFilter } from '../../api/types';
import { ErrorMessage } from '../../ui/ErrorMessage';
import { useTicketList } from './queries';
import { TicketFilters } from './TicketFilters';
import { TicketRow } from './TicketRow';

export const NO_FILTER: TicketFilter = { status: '', team: '', q: '' };

/** The tickets that match the filters, one server page (50 tickets) at a time. */
export function TicketList({ selectedId }: { selectedId: string | null }) {
  const [filter, setFilter] = useState<TicketFilter>(NO_FILTER);
  const list = useTicketList(filter);
  const tickets = list.data?.pages.flatMap((p) => p.items) ?? [];

  return (
    <section className="list" aria-labelledby="list-heading">
      <h2 id="list-heading">Tickets</h2>
      <TicketFilters value={filter} onChange={setFilter} />
      {list.isPending && <p className="muted">Loading tickets…</p>}
      {list.isError && <ErrorMessage error={list.error} onRetry={() => list.refetch()} />}
      {list.isSuccess && (
        <>
          <p className="muted" aria-live="polite">
            {tickets.length === 0
              ? 'No ticket matches.'
              : `Showing ${tickets.length} tickets${list.hasNextPage ? ' (more on the server)' : ''}.`}
            {list.isPlaceholderData && ' Updating…'}
          </p>
          <ul className="rows">
            {tickets.map((t) => (
              <li key={t.ticket_id}>
                <TicketRow ticket={t} selected={t.ticket_id === selectedId} />
              </li>
            ))}
          </ul>
          {list.hasNextPage && (
            <button type="button" className="secondary" onClick={() => list.fetchNextPage()} disabled={list.isFetchingNextPage}>
              {list.isFetchingNextPage ? 'Loading…' : 'Load 50 more'}
            </button>
          )}
        </>
      )}
    </section>
  );
}
