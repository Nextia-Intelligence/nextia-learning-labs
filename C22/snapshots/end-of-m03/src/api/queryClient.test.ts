import { expect, test } from 'vitest';
import { ApiError } from './client';
import { shouldRetry } from './queryClient';

test('retries a busy server or a lost connection, at most twice', () => {
  expect(shouldRetry(0, new ApiError(503, 'unavailable', 'Busy.'))).toBe(true);
  expect(shouldRetry(1, new ApiError(0, 'network_error', 'No answer.'))).toBe(true);
  expect(shouldRetry(2, new ApiError(503, 'unavailable', 'Busy.'))).toBe(false);
});

test('never retries an answer that will not change: 4xx', () => {
  expect(shouldRetry(0, new ApiError(404, 'not_found', 'No ticket.'))).toBe(false);
  expect(shouldRetry(0, new ApiError(422, 'invalid_request', 'Not valid.'))).toBe(false);
});
