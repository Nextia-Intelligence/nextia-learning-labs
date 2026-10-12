import { useState, type FormEvent } from 'react';
import { ApiError } from '../../api/client';
import { createTicket } from '../../api/tickets';
import type { NewTicket, TicketAccepted } from '../../api/types';
import { JobStatus } from './JobStatus';

const EMPTY: NewTicket = { customer_id: '', subject: '', body: '' };

/** The checks that the browser can do before it sends the form. The API checks again. */
export function validate(t: NewTicket): Partial<Record<keyof NewTicket, string>> {
  const errors: Partial<Record<keyof NewTicket, string>> = {};
  if (!/^C-\d{4,5}$/.test(t.customer_id.trim())) errors.customer_id = 'Write a customer ID such as C-0022.';
  if (!t.subject.trim()) errors.subject = 'Write a subject.';
  else if (t.subject.length > 120) errors.subject = 'Use 120 characters or fewer.';
  if (!t.body.trim()) errors.body = 'Write the customer’s message.';
  return errors;
}

/** A form for a ticket that came in by phone. Every input is controlled: React state owns its value. */
export function NewTicketForm() {
  const [values, setValues] = useState<NewTicket>(EMPTY);
  const [errors, setErrors] = useState<ReturnType<typeof validate>>({});
  const [sending, setSending] = useState(false);
  const [answer, setAnswer] = useState<TicketAccepted | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  // One key per ticket: if the agent sends the same form again after a network error, the API
  // recognizes it and does not save a second ticket.
  const [idempotencyKey, setIdempotencyKey] = useState(() => crypto.randomUUID());

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const found = validate(values);
    setErrors(found);
    if (Object.keys(found).length > 0) return;
    setSending(true);
    setFailure(null);
    try {
      setAnswer(await createTicket({ ...values, customer_id: values.customer_id.trim() }, idempotencyKey));
      setValues(EMPTY);
      setIdempotencyKey(crypto.randomUUID());
    } catch (error) {
      setFailure(error instanceof ApiError ? error.message : 'The ticket was not sent.');
    } finally {
      setSending(false);
    }
  }

  const field = (name: keyof NewTicket) => ({
    id: `new-${name}`,
    value: values[name],
    'aria-invalid': errors[name] ? true : undefined,
    'aria-describedby': errors[name] ? `new-${name}-error` : undefined,
    onChange: (e: { target: { value: string } }) => {
      setValues({ ...values, [name]: e.target.value });
      setIdempotencyKey(crypto.randomUUID()); // other content: another ticket
    },
  });
  const error = (name: keyof NewTicket) =>
    errors[name] && (
      <p className="field-error" id={`new-${name}-error`}>
        {errors[name]}
      </p>
    );

  return (
    <section className="card" aria-labelledby="new-heading">
      <h2 id="new-heading">New ticket</h2>
      <form onSubmit={onSubmit} noValidate className="form">
        <label htmlFor="new-customer_id">Customer ID</label>
        <input {...field('customer_id')} placeholder="C-0022" />
        {error('customer_id')}
        <label htmlFor="new-subject">Subject</label>
        <input {...field('subject')} />
        {error('subject')}
        <label htmlFor="new-body">Message</label>
        <textarea {...field('body')} rows={4} />
        {error('body')}
        <button type="submit" disabled={sending}>
          {sending ? 'Sending…' : 'Send ticket'}
        </button>
      </form>
      {failure && (
        <p className="error" role="alert">
          {failure}
        </p>
      )}
      {answer && (
        <>
          <p className="success">Saved as {answer.ticket_id}.</p>
          <JobStatus key={answer.job_id} jobId={answer.job_id} estimatedSeconds={answer.estimated_wait_seconds} />
        </>
      )}
    </section>
  );
}
