import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test, vi } from 'vitest';
import { apiError, installFakeApi } from '../../test/fakeApi';
import { fullDraft, openStream, sseResponse } from '../../test/stream';
import { DraftPanel } from './DraftPanel';

const tokens: [string, unknown][] = [
  ['start', { model: 'chat-small' }],
  ['token', { text: 'Your refund' }],
  ['token', { text: ' is on its way.' }],
];

test('shows the streamed text, then the checks and the sources', async () => {
  installFakeApi(() => sseResponse([...tokens, ['done', fullDraft]]));
  const onUse = vi.fn();
  render(<DraftPanel ticketId="T-64979" onUse={onUse} />);
  await userEvent.click(screen.getByRole('button', { name: 'Write a draft' }));
  expect(await screen.findByText('Draft finished. Check it before you use it.')).toBeInTheDocument();
  expect(screen.getByText('Your refund is on its way.')).toBeInTheDocument();
  expect(screen.getByText(/within 2 business days/, { selector: 'blockquote' })).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: 'Use this draft' }));
  expect(onUse).toHaveBeenCalledWith('Your refund is on its way.');
});

test('Stop ends the stream and says that the text is not complete', async () => {
  installFakeApi((_url, init) => openStream(tokens, init.signal));
  render(<DraftPanel ticketId="T-64979" onUse={() => {}} />);
  await userEvent.click(screen.getByRole('button', { name: 'Write a draft' }));
  await userEvent.click(await screen.findByRole('button', { name: 'Stop' }));
  expect(screen.getByText(/You stopped the draft/)).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Use this draft' })).not.toBeInTheDocument();
});

test('a connection that ends early is an interruption, not a finished draft', async () => {
  installFakeApi(() => sseResponse(tokens, { endEarly: true }));
  render(<DraftPanel ticketId="T-64979" onUse={() => {}} />);
  await userEvent.click(screen.getByRole('button', { name: 'Write a draft' }));
  expect(await screen.findByText(/The connection ended before the draft was finished/)).toBeInTheDocument();
});

test('an error event is a failure, in words', async () => {
  installFakeApi(() => sseResponse([...tokens.slice(0, 2), ['error', { error: { code: 'ai_unavailable', message: 'x' } }]]));
  render(<DraftPanel ticketId="T-64979" onUse={() => {}} />);
  await userEvent.click(screen.getByRole('button', { name: 'Write a draft' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('The AI service stopped answering');
});

test('a draft whose final text differs from the stream is refused', async () => {
  installFakeApi(() => sseResponse([...tokens, ['done', { ...fullDraft, reply: 'Something else.' }]]));
  render(<DraftPanel ticketId="T-64979" onUse={() => {}} />);
  await userEvent.click(screen.getByRole('button', { name: 'Write a draft' }));
  expect(await screen.findByText('The draft did not pass the checks. Do not use it.')).toBeInTheDocument();
});

test('a ticket without a draft says so', async () => {
  installFakeApi(() => apiError(404, 'no_draft', 'No AI draft exists for this ticket.'));
  render(<DraftPanel ticketId="T-30001" onUse={() => {}} />);
  await userEvent.click(screen.getByRole('button', { name: 'Write a draft' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Write the reply yourself');
});
