import { expect, test } from 'vitest';
import { parseRoute } from './router';

test('the address after # names the page', () => {
  expect(parseRoute('')).toEqual({ page: 'tickets', ticketId: null });
  expect(parseRoute('#/tickets/T-80008')).toEqual({ page: 'tickets', ticketId: 'T-80008' });
  expect(parseRoute('#/new')).toEqual({ page: 'new' });
  expect(parseRoute('#/labs/race')).toEqual({ page: 'labs', lab: 'race' });
});
