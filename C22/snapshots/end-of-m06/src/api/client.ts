// The one place that talks HTTP to the ticket API: the address, JSON, and the error shape.

export const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8100';

/** An error answer of the API, with its stable code (the contract's error shape). */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly fields: string[] = [],
    readonly retryAfter: number | null = null,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/** Sends a request and gives back the JSON answer, or throws an ApiError. */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { ...(init.body ? { 'Content-Type': 'application/json' } : {}), ...init.headers },
    });
  } catch (error) {
    if ((error as Error).name === 'AbortError') throw error;
    throw new ApiError(0, 'network_error', 'The ticket service did not answer. Check your connection.');
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const e = body?.error;
    const retry = response.headers.get('Retry-After');
    throw new ApiError(
      response.status,
      e?.code ?? 'unknown_error',
      e?.message ?? `The ticket service answered ${response.status}.`,
      e?.fields ?? [],
      retry ? Number(retry) : null,
    );
  }
  return body as T;
}
