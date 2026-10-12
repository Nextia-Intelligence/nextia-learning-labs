import { useEffect, useRef, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { TicketFilter } from '../../api/types';
import { ErrorMessage } from '../../ui/ErrorMessage';
import { useTicketList } from './queries';
import { TicketFilters } from './TicketFilters';
import { TicketRow } from './TicketRow';

export const NO_FILTER: TicketFilter = { status: '', team: '', q: '' };
const ROW_HEIGHT = 56; // px, the height of .row in styles.css (3.5rem)

/**
 * The tickets that match the filters, one server page (50 tickets) at a time. Only the rows in
 * view are in the page (virtualization): 50 or 5,000 loaded tickets cost the same to draw.
 */
export function TicketList({ selectedId }: { selectedId: string | null }) {
  const [filter, setFilter] = useState<TicketFilter>(NO_FILTER);
  const list = useTicketList(filter);
  const tickets = list.data?.pages.flatMap((p) => p.items) ?? [];
  const scroller = useRef<HTMLDivElement>(null);
  const rows = useVirtualizer({
    count: tickets.length,
    getScrollElement: () => scroller.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 8,
  });
  const visible = rows.getVirtualItems();

  // Near the end of what is loaded: ask the server for the next page.
  const last = visible.at(-1)?.index ?? 0;
  const { hasNextPage, isFetchingNextPage, fetchNextPage } = list;
  useEffect(() => {
    if (hasNextPage && !isFetchingNextPage && last >= tickets.length - 10) void fetchNextPage();
  }, [last, tickets.length, hasNextPage, isFetchingNextPage, fetchNextPage]);

  // A mark for the browser's performance tools: the first time that ticket rows are on the screen.
  const firstRows = tickets.length > 0;
  useEffect(() => {
    if (firstRows && performance.getEntriesByName('tickets:first-rows').length === 0) performance.mark('tickets:first-rows');
  }, [firstRows]);

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
          <div ref={scroller} className="scroller" tabIndex={0} role="region" aria-label="Ticket list">
            <ul className="rows" style={{ height: rows.getTotalSize(), position: 'relative' }}>
              {visible.map((v) => {
                const t = tickets[v.index];
                return (
                  <li
                    key={t.ticket_id}
                    style={{ position: 'absolute', top: 0, left: 0, right: 0, transform: `translateY(${v.start}px)` }}
                  >
                    <TicketRow ticket={t} selected={t.ticket_id === selectedId} />
                  </li>
                );
              })}
            </ul>
          </div>
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
