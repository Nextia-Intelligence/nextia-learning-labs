// Tests for the requests, with a fake fetch: no API needs to run.
import { afterEach, expect, test, vi } from 'vitest';
import { loadTickets, sendTicket, ticketLine } from './api';

afterEach(() => vi.unstubAllGlobals());

const ticket = {
  ticket_id: 'T-80008', customer_id: 'C-0022', customer_name: 'Ana Silva', subject: 'Parcel lost',
  team: 'shipping', priority: 2, status: 'open', created_at: '2026-01-05T10:00:00Z',
};

test('loadTickets asks for one page and gives back its tickets', async () => {
  const fetch = vi.fn(async () => new Response(JSON.stringify({ items: [ticket], next: null })));
  vi.stubGlobal('fetch', fetch);
  expect(await loadTickets(10)).toEqual([ticket]);
  expect(fetch).toHaveBeenCalledWith('http://127.0.0.1:8100/v1/tickets?limit=10');
});

test('loadTickets fails with the status when the API answers an error', async () => {
  vi.stubGlobal('fetch', async () => new Response('{}', { status: 503 }));
  await expect(loadTickets(10)).rejects.toThrow('The API answered 503');
});

test('sendTicket gives back the API error in words', async () => {
  const body = { error: { code: 'validation_error', message: 'The ticket is not valid.', request_id: 'r1', fields: ['customer_id'] } };
  vi.stubGlobal('fetch', async () => new Response(JSON.stringify(body), { status: 422 }));
  expect(await sendTicket({ customer_id: 'x', subject: 's', body: 'b' })).toBe('Not saved: The ticket is not valid. Fields: customer_id');
});

test('ticketLine shows the id, the subject and the status', () => {
  expect(ticketLine(ticket)).toBe('T-80008: Parcel lost (Ana Silva · shipping · open)');
});
