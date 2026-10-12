import { expect, test } from 'vitest';
import { checkDraft } from './drafts';

const good = { reply: 'Hi.', needs_human: false, citations: [], confidence: 'high' };

test('accepts a complete draft that is the text we saw', () => {
  expect(checkDraft(good, 'Hi.').ok).toBe(true);
});

test('refuses a draft with missing fields, or with other text than the stream', () => {
  expect(checkDraft({ reply: 'Hi.' }, 'Hi.')).toEqual({ ok: false, problem: 'The draft is not complete.' });
  expect(checkDraft(good, 'Hi')).toEqual({ ok: false, problem: 'The final draft is not the text that was shown.' });
});
