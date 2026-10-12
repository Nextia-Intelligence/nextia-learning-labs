import type { DraftStatus } from './draftMachine';
import { Citations } from './Citations';
import { useDraftStream } from './useDraftStream';

const STATUS_TEXT: Record<DraftStatus, string> = {
  idle: 'No draft yet.',
  connecting: 'Asking for a draft…',
  streaming: 'Writing the draft…',
  done: 'Draft finished. Check it before you use it.',
  stopped: 'You stopped the draft. The text below is not complete.',
  interrupted: 'The connection ended before the draft was finished. The text below is not complete.',
  failed: 'No draft.',
  invalid: 'The draft did not pass the checks. Do not use it.',
};

/** The AI draft of a reply: streamed as it is written, with Stop, its checks and its sources. */
export function DraftPanel({ ticketId, onUse }: { ticketId: string; onUse: (text: string) => void }) {
  const { state, start, stop, reset } = useDraftStream(ticketId);
  const running = state.status === 'connecting' || state.status === 'streaming';
  const unfinished = state.status === 'stopped' || state.status === 'interrupted';

  return (
    <section className="draft" aria-labelledby="draft-heading" data-status={state.status}>
      <h3 id="draft-heading">AI draft</h3>
      <p className="draft-state">{STATUS_TEXT[state.status]}</p>
      {state.problem && (
        <p className="error" role="alert">
          {state.problem}
        </p>
      )}
      {state.text && <div className={unfinished ? 'draft-text muted' : 'draft-text'}>{state.text}</div>}

      {state.status === 'done' && state.draft && (
        <>
          {state.draft.needs_human ? (
            <p className="notice">
              <strong>A person must handle this ticket.</strong> {state.draft.reason}
            </p>
          ) : (
            <p className="muted">Why: {state.draft.reason}</p>
          )}
          {state.draft.confidence !== 'high' && (
            <p className="notice">The assistant is not sure about this draft (confidence: {state.draft.confidence}).</p>
          )}
          <Citations draft={state.draft} />
        </>
      )}

      <div className="toolbar">
        {running ? (
          <button type="button" onClick={stop}>
            Stop
          </button>
        ) : (
          <button type="button" onClick={start}>
            {state.status === 'idle' ? 'Write a draft' : 'Write a new draft'}
          </button>
        )}
        {state.status === 'done' && state.draft && (
          <button type="button" className="secondary" onClick={() => onUse(state.draft!.reply)}>
            Use this draft
          </button>
        )}
        {!running && state.status !== 'idle' && (
          <button type="button" className="secondary" onClick={reset}>
            Discard
          </button>
        )}
      </div>
      <p className="muted">
        Drafts come from an AI model. They can be wrong. You decide what to send.
      </p>
    </section>
  );
}
