// The cache of server data (TanStack Query) and its rules for this app.
import { QueryClient } from '@tanstack/react-query';
import { ApiError } from './client';

/** Try again only when trying again can help: no answer, or the server is busy (503). Never for 4xx. */
export function shouldRetry(failureCount: number, error: Error): boolean {
  if (!(error instanceof ApiError)) return false;
  const temporary = error.code === 'network_error' || error.status === 503;
  return temporary && failureCount < 2;
}

export function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000, // an answer counts as fresh for 30 s: no new request in that time
        gcTime: 5 * 60_000, // an answer that no screen uses stays in the cache for 5 minutes
        retry: shouldRetry,
        retryDelay: (attempt, error) =>
          error instanceof ApiError && error.retryAfter ? error.retryAfter * 1000 : 500 * 2 ** attempt,
        refetchOnWindowFocus: true,
      },
      mutations: { retry: false }, // a change is never sent twice by itself
    },
  });
}
