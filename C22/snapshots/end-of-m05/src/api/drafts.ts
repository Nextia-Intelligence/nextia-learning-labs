// The AI draft of a reply, streamed by the API as server-sent events: start, token …, done or error.
import { API_URL, ApiError } from './client';
import { SseParser } from './sse';

export interface Citation {
  id: string;
  claim: string;
  document: string;
  version: string;
  section: string;
  quote: string;
}

export interface Draft {
  ticket_id: string;
  model: string;
  language: string;
  needs_human: boolean;
  reason: string;
  confidence: 'high' | 'medium' | 'low';
  suggested_team: string;
  reply: string;
  citations: Citation[];
  policy_answer: { question: string; answerable: boolean; answer: string } | null;
  recorded_ms: number;
}

export type StreamEvent =
  | { type: 'start'; model: string }
  | { type: 'token'; text: string }
  | { type: 'done'; draft: unknown }
  | { type: 'error'; error: ApiError };

/**
 * Streams the draft of one ticket. Calls onEvent for every event, in order. Resolves when the
 * stream ends; rejects with an AbortError when the signal stops it, or with an ApiError.
 */
export async function streamDraft(
  ticketId: string,
  onEvent: (e: StreamEvent) => void,
  signal: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/v1/tickets/${ticketId}/draft`, {
      method: 'POST',
      headers: { Accept: 'text/event-stream' },
      signal,
    });
  } catch (error) {
    if ((error as Error).name === 'AbortError') throw error;
    throw new ApiError(0, 'network_error', 'The ticket service did not answer. Check your connection.');
  }
  if (!response.ok || !response.body) {
    const e = (await response.json().catch(() => null))?.error;
    throw new ApiError(response.status, e?.code ?? 'unknown_error', e?.message ?? `The ticket service answered ${response.status}.`);
  }
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  const parser = new SseParser();
  for (;;) {
    let piece: ReadableStreamReadResult<string>;
    try {
      piece = await reader.read();
    } catch (error) {
      if ((error as Error).name === 'AbortError') throw error;
      throw new ApiError(0, 'network_error', 'The connection to the ticket service was lost.');
    }
    const { value, done } = piece;
    if (done) return;
    for (const e of parser.push(value)) {
      const data = JSON.parse(e.data);
      if (e.event === 'start') onEvent({ type: 'start', model: data.model });
      else if (e.event === 'token') onEvent({ type: 'token', text: data.text });
      else if (e.event === 'done') onEvent({ type: 'done', draft: data });
      else if (e.event === 'error') {
        onEvent({ type: 'error', error: new ApiError(200, data.error.code, data.error.message) });
      }
    }
  }
}

/** Checks the final draft before the screen trusts it: the shape, and that it is the text we saw. */
export function checkDraft(value: unknown, streamedText: string): { ok: true; draft: Draft } | { ok: false; problem: string } {
  const d = value as Partial<Draft> | null;
  if (!d || typeof d.reply !== 'string' || typeof d.needs_human !== 'boolean' || !Array.isArray(d.citations)) {
    return { ok: false, problem: 'The draft is not complete.' };
  }
  if (!['high', 'medium', 'low'].includes(String(d.confidence))) return { ok: false, problem: 'The draft has no confidence.' };
  if (d.reply !== streamedText) return { ok: false, problem: 'The final draft is not the text that was shown.' };
  return { ok: true, draft: d as Draft };
}
