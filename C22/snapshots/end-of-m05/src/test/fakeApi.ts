// A fake ticket API for component tests: it replaces fetch, so no server runs.
// Each test says which answer every request gets.
import { vi } from 'vitest';
import type { TicketSummary } from '../api/types';

export type Handler = (url: URL, init: RequestInit) => Response | Promise<Response>;

export function json(status: number, body: unknown, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', ...headers } });
}

export function apiError(status: number, code: string, message: string, fields: string[] = [], headers = {}) {
  return json(status, { error: { code, message, request_id: 'test', fields } }, headers);
}

/** Replaces fetch. Gives back the mock function, to check the requests that were sent. */
export function installFakeApi(handler: Handler) {
  const fake = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = new URL(String(input));
    if (init.signal?.aborted) throw new DOMException('The request was cancelled.', 'AbortError');
    const answer = handler(url, init);
    if (!init.signal) return answer;
    // Like the browser: a cancelled request rejects with an AbortError.
    return Promise.race([
      answer,
      new Promise<Response>((_, reject) =>
        init.signal!.addEventListener('abort', () => reject(new DOMException('The request was cancelled.', 'AbortError'))),
      ),
    ]);
  });
  vi.stubGlobal('fetch', fake);
  return fake;
}

/** A promise that the test resolves later: it controls the order in which answers arrive. */
export function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => (resolve = r));
  return { promise, resolve };
}

export function ticket(n: number, over: Partial<TicketSummary> = {}): TicketSummary {
  return {
    ticket_id: `T-${30000 + n}`,
    customer_id: 'C-0022',
    customer_name: 'Emma Costa',
    subject: `Ticket number ${n}`,
    team: 'billing',
    priority: 2,
    status: 'open',
    created_at: '2026-10-10T08:00:00Z',
    message_count: 0,
    last_message_at: null,
    ...over,
  };
}
