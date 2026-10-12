import { getTicket } from '../../api/tickets';
import { useApi } from '../../lib/useApi';
import { ErrorMessage } from '../../ui/ErrorMessage';
import { StatusBadge } from '../../ui/StatusBadge';

/** One ticket: the customer's message and the conversation. */
export function TicketView({ ticketId }: { ticketId: string }) {
  const ticket = useApi((signal) => getTicket(ticketId, signal), [ticketId]);

  if (ticket.status === 'loading') return <p className="muted">Loading {ticketId}…</p>;
  if (ticket.status === 'error') return <ErrorMessage error={ticket.error} />;
  const t = ticket.data;
  return (
    <article className="ticket" aria-labelledby="ticket-heading">
      <header>
        <p className="muted">
          {t.ticket_id} · {t.customer_name} ({t.customer_id}) · {t.team} · priority {t.priority}
        </p>
        <h2 id="ticket-heading">{t.subject}</h2>
        <StatusBadge status={t.status} />
      </header>
      <section aria-label="Conversation">
        <div className="message message-customer">
          <p className="muted">Customer</p>
          <p>{t.body || '(no text)'}</p>
        </div>
        {t.messages.map((m) => (
          <div key={m.message_id} className={`message message-${m.author}`}>
            <p className="muted">{m.author === 'agent' ? 'Agent' : 'Customer'}</p>
            <p>{m.body}</p>
          </div>
        ))}
      </section>
    </article>
  );
}
