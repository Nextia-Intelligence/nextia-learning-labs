// A fake streamed answer: server-sent events that arrive in pieces, as from the network.
import { json } from './fakeApi';

export function sseResponse(events: [string, unknown][], options: { endEarly?: boolean } = {}): Response {
  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const [event, data] of events) controller.enqueue(encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`));
      // The network ends the stream a moment later (an error at once would drop the queued events).
      if (options.endEarly) setTimeout(() => controller.error(new TypeError('network connection lost')), 20);
      else controller.close();
    },
  });
  return new Response(body, { status: 200, headers: { 'Content-Type': 'text/event-stream' } });
}

/** A stream that sends the first events, then waits for ever (until the request is stopped). */
export function openStream(events: [string, unknown][], signal?: AbortSignal | null): Response {
  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const [event, data] of events) controller.enqueue(encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`));
      signal?.addEventListener('abort', () => controller.error(new DOMException('stopped', 'AbortError')));
    },
  });
  return new Response(body, { status: 200, headers: { 'Content-Type': 'text/event-stream' } });
}

export const fullDraft = {
  ticket_id: 'T-64979',
  model: 'chat-small',
  language: 'en',
  needs_human: false,
  reason: 'A refund question belongs to the returns team.',
  confidence: 'high',
  suggested_team: 'returns',
  reply: 'Your refund is on its way.',
  citations: [
    {
      id: '2e762c0284bb',
      claim: 'The refund is sent within 2 business days after approval.',
      document: 'Refunds and payments policy',
      version: 'policy, version 3',
      section: 'How long a refund takes',
      quote: 'When a refund is approved, we send it to the original payment method within 2 business days.',
    },
  ],
  policy_answer: { question: 'How long does a refund take?', answerable: true, answer: '…' },
  recorded_ms: 2000,
};

export { json };
