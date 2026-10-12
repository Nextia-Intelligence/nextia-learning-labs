import { useState, type FormEvent } from 'react';
import { useAddMessage } from './queries';

/** The agent's answer to the customer. It is checked before it is sent, and sent only once. */
export function MessageForm({ ticketId, initialText = '' }: { ticketId: string; initialText?: string }) {
  const [text, setText] = useState(initialText);
  const [problem, setProblem] = useState<string | null>(null);
  const send = useAddMessage(ticketId);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!text.trim()) return setProblem('Write a message first.');
    if (text.length > 5000) return setProblem('Use 5,000 characters or fewer.');
    setProblem(null);
    send.mutate(text, { onSuccess: () => setText('') });
  }

  return (
    <form onSubmit={onSubmit} className="form" noValidate>
      <label htmlFor="reply">Reply to the customer</label>
      <textarea
        id="reply"
        rows={4}
        value={text}
        onChange={(e) => setText(e.target.value)}
        aria-invalid={problem ? true : undefined}
        aria-describedby={problem ? 'reply-error' : undefined}
      />
      {problem && (
        <p className="field-error" id="reply-error">
          {problem}
        </p>
      )}
      <div className="toolbar">
        <button type="submit" disabled={send.isPending}>
          {send.isPending ? 'Sending…' : 'Send reply'}
        </button>
        {send.isSuccess && <span role="status">Sent.</span>}
        {send.isError && (
          <span className="error" role="alert">
            Not sent: {send.error.message}
          </span>
        )}
      </div>
    </form>
  );
}
