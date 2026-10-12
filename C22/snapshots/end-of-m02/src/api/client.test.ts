import { expect, test } from 'vitest';
import { apiError, installFakeApi, json } from '../test/fakeApi';
import { ApiError, apiFetch } from './client';

test('gives back the JSON of a good answer', async () => {
  installFakeApi(() => json(200, { status: 'ok' }));
  await expect(apiFetch('/health')).resolves.toEqual({ status: 'ok' });
});

test('turns the error shape into an ApiError with its code, fields and Retry-After', async () => {
  installFakeApi(() => apiError(503, 'unavailable', 'Not now.', [], { 'Retry-After': '2' }));
  const error = await apiFetch('/v1/tickets').catch((e) => e);
  expect(error).toBeInstanceOf(ApiError);
  expect(error).toMatchObject({ status: 503, code: 'unavailable', message: 'Not now.', retryAfter: 2 });
});

test('a server that does not answer is a network_error', async () => {
  installFakeApi(() => Promise.reject(new TypeError('Failed to fetch')));
  await expect(apiFetch('/health')).rejects.toMatchObject({ code: 'network_error' });
});
