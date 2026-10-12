import { useState } from 'react';
import { listTickets } from '../../api/tickets';
import type { TicketFilter } from '../../api/types';
import { useApi } from '../../lib/useApi';
import { ErrorMessage } from '../../ui/ErrorMessage';
import { TicketFilters } from './TicketFilters';
import { TicketRow } from './TicketRow';

export const NO_FILTER: TicketFilter = { status: '', team: '', q: '' };

/** The first 50 tickets that match the filters. The filters are this component's own state. */
export function TicketList({ selectedId }: { selectedId: string | null }) {
  const [filter, setFilter] = useState<TicketFilter>(NO_FILTER);
  const tickets = useApi((signal) => listTickets(filter, 50, null, signal), [filter.status, filter.team, filter.q]);

  return (
    <section className="list" aria-labelledby="list-heading">
      <h2 id="list-heading">Tickets</h2>
      <TicketFilters value={filter} onChange={setFilter} />
      {tickets.status === 'loading' && <p className="muted">Loading tickets…</p>}
      {tickets.status === 'error' && <ErrorMessage error={tickets.error} />}
      {tickets.status === 'success' && (
        <>
          <p className="muted">{tickets.data.items.length === 0 ? 'No ticket matches.' : `Showing ${tickets.data.items.length} tickets.`}</p>
          <ul className="rows">
            {tickets.data.items.map((t) => (
              <li key={t.ticket_id}>
                <TicketRow ticket={t} selected={t.ticket_id === selectedId} />
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
