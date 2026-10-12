import { act, renderHook, waitFor } from '@testing-library/react';
import { expect, test } from 'vitest';
import { deferred } from '../test/fakeApi';
import { useApi } from './useApi';

test('shows loading, then the data', async () => {
  const { result } = renderHook(() => useApi(async () => 'tickets', []));
  expect(result.current.status).toBe('loading');
  await waitFor(() => expect(result.current).toMatchObject({ status: 'success', data: 'tickets' }));
});

test('an old answer that arrives late does not replace the new one', async () => {
  const slow = deferred<string>();
  const fast = deferred<string>();
  const answers: Record<string, Promise<string>> = { p: slow.promise, parcel: fast.promise };
  const { result, rerender } = renderHook(({ q }) => useApi(() => answers[q], [q]), { initialProps: { q: 'p' } });
  rerender({ q: 'parcel' });
  await act(async () => fast.resolve('results for parcel'));
  await act(async () => slow.resolve('results for p'));
  expect(result.current.data).toBe('results for parcel');
});

test('the cleanup cancels the request when the inputs change', async () => {
  const signals: AbortSignal[] = [];
  const { rerender } = renderHook(({ id }) => useApi((signal) => (signals.push(signal), new Promise(() => {})), [id]), {
    initialProps: { id: 1 },
  });
  rerender({ id: 2 });
  expect(signals[0].aborted).toBe(true);
  expect(signals[1].aborted).toBe(false);
});
