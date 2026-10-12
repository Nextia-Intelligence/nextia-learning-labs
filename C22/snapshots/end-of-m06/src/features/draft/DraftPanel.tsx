import { lazy, Suspense } from 'react';
import { LiveRegion } from '../../ui/LiveRegion';
import { Citations } from './Citations';
import type { DraftState, DraftStatus } from './draftMachine';
import { useDraftStream } from './useDraftStream';

// The Markdown tools (marked, DOMPurify) are loaded only when a draft is finished.
const DraftText = lazy(() => import('./DraftText'));

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

/** What a screen reader hears: one sentence when the state changes, never the streamed text. */
export function announcement(s: DraftState): string {
  if (s.status === 'done' && s.draft) {
    const sources = s.draft.citations.length;
    return [
      'Draft finished.',
      sources ? `${sources} ${sources === 1 ? 'source' : 'sources'}.` : 'No sources.',
      s.draft.needs_human ? 'A person must handle this ticket.' : '',
    ].join(' ').trim();
  }
  if (s.status === 'failed' || s.status === 'invalid') return `${STATUS_TEXT[s.status]} ${s.problem ?? ''}`.trim();
  if (s.status === 'idle') return '';
  return STATUS_TEXT[s.status];
}

/** The AI draft of a reply: streamed as it is written, with Stop, its checks and its sources. */
export function DraftPanel({ ticketId, onUse }: { ticketId: string; onUse: (text: string) => void }) {
  const { state, start, stop, reset } = useDraftStream(ticketId);
  const running = state.status === 'connecting' || state.status === 'streaming';
  const unfinished = state.status === 'stopped' || state.status === 'interrupted';

  return (
    <section className="draft" aria-labelledby="draft-heading" data-status={state.status}>
      <h3 id="draft-heading">AI draft</h3>
      <p className="draft-state" aria-hidden="true">
        {STATUS_TEXT[state.status]}
      </p>
      <LiveRegion message={announcement(state)} />
      {state.problem && <p className="error">{state.problem}</p>}
      {state.status === 'done' && state.draft ? (
        <Suspense fallback={<div className="draft-text">{state.text}</div>}>
          <DraftText text={state.draft.reply} />
        </Suspense>
      ) : (
        state.text && (
          <div className={unfinished ? 'draft-text muted' : 'draft-text'} aria-busy={running}>
            {state.text}
          </div>
        )
      )}

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
        {/* One button that changes its label: the keyboard focus stays on it when the stream
            starts and ends. Two different buttons would drop the focus to the top of the page. */}
        <button type="button" onClick={running ? stop : start}>
          {running ? 'Stop' : state.status === 'idle' ? 'Write a draft' : 'Write a new draft'}
        </button>
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
      <p className="muted">Drafts come from an AI model. They can be wrong. You decide what to send.</p>
    </section>
  );
}
