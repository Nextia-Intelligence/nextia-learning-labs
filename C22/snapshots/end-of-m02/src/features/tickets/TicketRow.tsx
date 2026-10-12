import type { TicketSummary } from '../../api/types';
import { StatusBadge } from '../../ui/StatusBadge';

/** One ticket in the list: a link that opens the ticket. */
export function TicketRow({ ticket, selected }: { ticket: TicketSummary; selected: boolean }) {
  return (
    <a className="row" href={`#/tickets/${ticket.ticket_id}`} aria-current={selected ? 'true' : undefined}>
      <span className="row-id">{ticket.ticket_id}</span>
      <span className="row-subject">{ticket.subject}</span>
      <span className="row-meta">
        {ticket.customer_name} · {ticket.team}
      </span>
      <StatusBadge status={ticket.status} />
    </a>
  );
}
