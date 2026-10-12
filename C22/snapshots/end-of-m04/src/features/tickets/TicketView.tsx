import { useState } from 'react';
import { ErrorMessage } from '../../ui/ErrorMessage';
import { DraftPanel } from '../draft/DraftPanel';
import { MessageForm } from './MessageForm';
import { useTicket } from './queries';
import { StatusSelect } from './StatusSelect';

/** One ticket: the customer's message, the conversation, the status, the AI draft and the reply form. */
export function TicketView({ ticketId }: { ticketId: string }) {
  const ticket = useTicket(ticketId);
  // "Use this draft" puts the draft into the reply form; the counter makes a new form each time.
  const [prefill, setPrefill] = useState({ ticketId: '', text: '', n: 0 });

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
      {t.has_draft ? (
        <DraftPanel key={t.ticket_id} ticketId={t.ticket_id} onUse={(text) => setPrefill((p) => ({ ticketId, text, n: p.n + 1 }))} />
      ) : (
        <p className="muted">No AI draft exists for this ticket.</p>
      )}
      <MessageForm key={`${t.ticket_id}-${prefill.n}`} ticketId={t.ticket_id} initialText={prefill.ticketId === ticketId ? prefill.text : ''} />
    </article>
  );
}
