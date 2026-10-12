import { ErrorMessage } from '../../ui/ErrorMessage';
import { MessageForm } from './MessageForm';
import { useTicket } from './queries';
import { StatusSelect } from './StatusSelect';

/** One ticket: the customer's message, the conversation, the status and the reply form. */
export function TicketView({ ticketId }: { ticketId: string }) {
  const ticket = useTicket(ticketId);

  if (ticket.isPending) return <p className="muted">Loading {ticketId}…</p>;
  if (ticket.isError) return <ErrorMessage error={ticket.error} onRetry={() => ticket.refetch()} />;
  const t = ticket.data;
  return (
    <article className="ticket" aria-labelledby="ticket-heading">
      <header>
        <p className="muted">
          {t.ticket_id} · {t.customer_name} ({t.customer_id}) · {t.team} · priority {t.priority}
        </p>
        <h2 id="ticket-heading">{t.subject}</h2>
        <StatusSelect ticketId={t.ticket_id} status={t.status} />
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
      <MessageForm key={t.ticket_id} ticketId={t.ticket_id} initialText="" />
    </article>
  );
}
