import { useCallback, useEffect, useReducer, useRef } from 'react';
import { checkDraft, streamDraft } from '../../api/drafts';
import { describeError } from '../../lib/errors';
import { draftReducer, initialDraft } from './draftMachine';

/** Streams one ticket's draft into the state machine. start() begins; stop() cancels the request. */
export function useDraftStream(ticketId: string) {
  const [state, dispatch] = useReducer(draftReducer, initialDraft);
  const controller = useRef<AbortController | null>(null);

  const start = useCallback(async () => {
    controller.current?.abort();
    const c = new AbortController();
    controller.current = c;
    dispatch({ type: 'start' });
    let text = '';
    let finished = false;
    try {
      await streamDraft(
        ticketId,
        (e) => {
          if (e.type === 'token') {
            text += e.text;
            dispatch({ type: 'token', text: e.text });
          } else if (e.type === 'done') {
            finished = true;
            const checked = checkDraft(e.draft, text);
            dispatch(checked.ok ? { type: 'done', draft: checked.draft } : { type: 'invalid', problem: checked.problem });
          } else if (e.type === 'error') {
            finished = true;
            dispatch({ type: 'fail', problem: describeError(e.error).text });
          }
        },
        c.signal,
      );
      if (!finished) dispatch({ type: 'ended' }); // the stream closed without "done" or "error"
    } catch (error) {
      if (c.signal.aborted) return; // stop() already set the state
      // A network error after the first piece is an interruption; before it, a failure.
      dispatch(text ? { type: 'ended' } : { type: 'fail', problem: describeError(error as Error).text });
    }
  }, [ticketId]);

  const stop = useCallback(() => {
    controller.current?.abort();
    dispatch({ type: 'stop' });
  }, []);

  const reset = useCallback(() => {
    controller.current?.abort();
    dispatch({ type: 'reset' });
  }, []);

  // A new ticket, or leaving the page: stop the stream of the old one.
  useEffect(() => () => controller.current?.abort(), [ticketId]);

  return { state, start, stop, reset };
}
