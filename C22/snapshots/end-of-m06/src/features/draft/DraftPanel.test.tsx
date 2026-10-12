import { render, screen, waitFor } from '@testing-library/react';
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
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Draft finished. 1 source.'));
  expect(await screen.findByText('Your refund is on its way.')).toBeInTheDocument();
  expect(screen.getByText(/within 2 business days/, { selector: 'blockquote' })).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: 'Use this draft' }));
  expect(onUse).toHaveBeenCalledWith('Your refund is on its way.');
});

test('Stop ends the stream and says that the text is not complete', async () => {
  installFakeApi((_url, init) => openStream(tokens, init.signal));
  render(<DraftPanel ticketId="T-64979" onUse={() => {}} />);
  await userEvent.click(screen.getByRole('button', { name: 'Write a draft' }));
  await userEvent.click(await screen.findByRole('button', { name: 'Stop' }));
  expect(screen.getByRole('status')).toHaveTextContent('You stopped the draft.');
  expect(screen.queryByRole('button', { name: 'Use this draft' })).not.toBeInTheDocument();
});

test('a connection that ends early is an interruption, not a finished draft', async () => {
  installFakeApi(() => sseResponse(tokens, { endEarly: true }));
  render(<DraftPanel ticketId="T-64979" onUse={() => {}} />);
  await userEvent.click(screen.getByRole('button', { name: 'Write a draft' }));
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent(/The connection ended before the draft was finished/));
});

test('an error event is a failure, in words', async () => {
  installFakeApi(() => sseResponse([...tokens.slice(0, 2), ['error', { error: { code: 'ai_unavailable', message: 'x' } }]]));
  render(<DraftPanel ticketId="T-64979" onUse={() => {}} />);
  await userEvent.click(screen.getByRole('button', { name: 'Write a draft' }));
  expect(await screen.findByRole('status')).toHaveTextContent('No draft. The AI service stopped answering');
});

test('a draft whose final text differs from the stream is refused', async () => {
  installFakeApi(() => sseResponse([...tokens, ['done', { ...fullDraft, reply: 'Something else.' }]]));
  render(<DraftPanel ticketId="T-64979" onUse={() => {}} />);
  await userEvent.click(screen.getByRole('button', { name: 'Write a draft' }));
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('The draft did not pass the checks. Do not use it.'));
});

test('a ticket without a draft says so', async () => {
  installFakeApi(() => apiError(404, 'no_draft', 'No AI draft exists for this ticket.'));
  render(<DraftPanel ticketId="T-30001" onUse={() => {}} />);
  await userEvent.click(screen.getByRole('button', { name: 'Write a draft' }));
  expect(await screen.findByRole('status')).toHaveTextContent('Write the reply yourself');
});

test('a screen reader hears the changes of state, never the streamed text', async () => {
  installFakeApi((_url, init) => openStream(tokens, init.signal));
  render(<DraftPanel ticketId="T-64979" onUse={() => {}} />);
  await userEvent.click(screen.getByRole('button', { name: 'Write a draft' }));
  expect(await screen.findByText('Your refund is on its way.')).toBeInTheDocument();
  expect(screen.getByRole('status')).toHaveTextContent(/^Writing the draft…$/);
});

test('the keyboard focus stays on the button when the stream starts and stops', async () => {
  installFakeApi((_url, init) => openStream(tokens, init.signal));
  render(<DraftPanel ticketId="T-64979" onUse={() => {}} />);
  screen.getByRole('button', { name: 'Write a draft' }).focus();
  await userEvent.keyboard('{Enter}');
  const stop = await screen.findByRole('button', { name: 'Stop' });
  expect(stop).toHaveFocus();
  await userEvent.keyboard('{Enter}');
  expect(screen.getByRole('button', { name: 'Write a new draft' })).toHaveFocus();
  expect(screen.getByRole('status')).toHaveTextContent('You stopped the draft.');
});

test('a finished draft shows its Markdown, without the HTML that runs code', async () => {
  const reply = 'See our [returns policy](https://example.com/returns). <img src=x onerror="alert(1)">';
  installFakeApi(() => sseResponse([['start', {}], ['token', { text: reply }], ['done', { ...fullDraft, reply }]]));
  const { container } = render(<DraftPanel ticketId="T-80010" onUse={() => {}} />);
  await userEvent.click(screen.getByRole('button', { name: 'Write a draft' }));
  expect(await screen.findByRole('link', { name: 'returns policy' })).toHaveAttribute('href', 'https://example.com/returns');
  expect(container.querySelector('img')).toBeNull();
});
