import { expect, test } from 'vitest';
import { ApiError } from '../api/client';
import { describeError } from './errors';

test('known codes become plain words, with whether to try again', () => {
  expect(describeError(new ApiError(404, 'no_draft', 'x'))).toEqual({
    text: 'No AI draft exists for this ticket. Write the reply yourself.',
    canRetry: false,
  });
  expect(describeError(new ApiError(503, 'unavailable', 'x', [], 2)).text).toBe('The ticket service is busy. Try again in 2 seconds.');
});

test('an unknown server error keeps its message and can be retried', () => {
  expect(describeError(new ApiError(500, 'internal_error', 'Boom.'))).toEqual({ text: 'Boom.', canRetry: true });
  expect(describeError(new Error('x')).canRetry).toBe(false);
});
