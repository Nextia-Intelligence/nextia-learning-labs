import { expect, test } from 'vitest';
import type { Draft } from '../../api/drafts';
import { draftReducer, initialDraft, type DraftAction, type DraftState } from './draftMachine';

const run = (actions: DraftAction[], from: DraftState = initialDraft) => actions.reduce(draftReducer, from);
const draft = { reply: 'Hello there' } as Draft;

test('a normal stream: connecting, streaming, done', () => {
  expect(run([{ type: 'start' }]).status).toBe('connecting');
  const s = run([{ type: 'start' }, { type: 'token', text: 'Hello' }, { type: 'token', text: ' there' }]);
  expect(s).toMatchObject({ status: 'streaming', text: 'Hello there', pieces: 2 });
  expect(draftReducer(s, { type: 'done', draft }).status).toBe('done');
});

test('stop, interruption and failure are three different end states', () => {
  const streaming = run([{ type: 'start' }, { type: 'token', text: 'Hel' }]);
  expect(draftReducer(streaming, { type: 'stop' })).toMatchObject({ status: 'stopped', text: 'Hel' });
  expect(draftReducer(streaming, { type: 'ended' }).status).toBe('interrupted');
  expect(draftReducer(streaming, { type: 'fail', problem: 'x' }).status).toBe('failed');
});

test('a late event after the end changes nothing', () => {
  const stopped = run([{ type: 'start' }, { type: 'token', text: 'Hel' }, { type: 'stop' }]);
  expect(run([{ type: 'token', text: 'lo' }, { type: 'done', draft }], stopped)).toBe(stopped);
});
