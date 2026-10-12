import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test } from 'vitest';
import type { Job } from '../../api/jobs';
import { installFakeApi, json } from '../../test/fakeApi';
import { renderWithCache } from '../../test/render';
import { JobStatus } from './JobStatus';

const job = (state: Job['state'], over: Partial<Job> = {}): Job => ({
  job_id: 1, ticket_id: 'T-500001', state, attempts: 1, max_attempts: 5, created_at: '', started_at: null,
  finished_at: null, last_error: null, result: null, ...over,
});

test('polls until the job is done, then stops asking', async () => {
  const states: Job[] = [job('queued'), job('running'), job('succeeded', { result: { team: 'shipping', priority: 2, draft_reply: null, embedding_version: null } })];
  const fake = installFakeApi(() => json(200, states.length > 1 ? states.shift() : states[0]));
  renderWithCache(<JobStatus jobId={1} />);
  expect(await screen.findByText('The AI work waits in the queue.')).toBeInTheDocument();
  expect(await screen.findByText('The AI work is done.', {}, { timeout: 4000 })).toBeInTheDocument();
  expect(screen.getByText('shipping')).toBeInTheDocument();
  const calls = fake.mock.calls.length;
  await new Promise((r) => setTimeout(r, 1200));
  expect(fake.mock.calls.length).toBe(calls);
});

test('failed and dead letter look different, and only a dead letter offers Try again', async () => {
  installFakeApi(() => json(200, job('failed', { last_error: 'ai_bad_answer' })));
  const first = renderWithCache(<JobStatus jobId={1} />);
  expect(await screen.findByText(/Trying again will not help/)).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Try again' })).not.toBeInTheDocument();
  first.unmount();
  installFakeApi((url) => json(200, url.pathname.endsWith('/retry') ? job('queued') : job('dead_letter', { attempts: 5 })));
  renderWithCache(<JobStatus jobId={1} />);
  await userEvent.click(await screen.findByRole('button', { name: 'Try again' }));
  expect(await screen.findByText('The AI work waits in the queue.')).toBeInTheDocument();
});

test('a queued job can be cancelled', async () => {
  installFakeApi((url) => json(200, url.pathname.endsWith('/cancel') ? job('cancelled') : job('queued')));
  renderWithCache(<JobStatus jobId={1} />);
  await userEvent.click(await screen.findByRole('button', { name: 'Cancel the AI work' }));
  expect(await screen.findByText(/You cancelled the AI work/)).toBeInTheDocument();
});
