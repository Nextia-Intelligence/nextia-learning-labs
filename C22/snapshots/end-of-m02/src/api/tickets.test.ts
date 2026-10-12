import { expect, test } from 'vitest';
import { listQuery } from './tickets';

test('the list query has only the filters that are set', () => {
  expect(listQuery({ status: '', team: '', q: '' }, 50)).toBe('limit=50');
  expect(listQuery({ status: 'open', team: 'billing', q: ' parcel ' }, 20, 'abc')).toBe(
    'limit=20&status=open&team=billing&q=parcel&after=abc',
  );
});
