import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test } from 'vitest';
import { installFakeApi, json } from '../../test/fakeApi';
import { renderWithCache } from '../../test/render';
import { NewTicketForm, validate } from './NewTicketForm';

test('validate names every field that is not valid', () => {
  expect(Object.keys(validate({ customer_id: 'x', subject: '', body: ' ' }))).toEqual(['customer_id', 'subject', 'body']);
  expect(validate({ customer_id: 'C-0022', subject: 'Parcel lost', body: 'It did not arrive.' })).toEqual({});
});

test('does not send a form with errors, and says what to fix', async () => {
  const fake = installFakeApi(() => json(202, {}));
  renderWithCache(<NewTicketForm />);
  await userEvent.click(screen.getByRole('button', { name: 'Send ticket' }));
  expect(screen.getByLabelText('Customer ID')).toHaveAttribute('aria-invalid', 'true');
  expect(screen.getByText('Write a subject.')).toBeInTheDocument();
  expect(fake).not.toHaveBeenCalled();
});

test('sends a valid form and shows the API’s answer', async () => {
  const fake = installFakeApi(() =>
    json(202, { ticket_id: 'T-500001', job_id: 1, state: 'queued', status_url: '/v1/jobs/1', queued_ahead: 0, estimated_wait_seconds: 3.7 }),
  );
  renderWithCache(<NewTicketForm />);
  await userEvent.type(screen.getByLabelText('Customer ID'), 'C-0022');
  await userEvent.type(screen.getByLabelText('Subject'), 'Parcel lost');
  await userEvent.type(screen.getByLabelText('Message'), 'It did not arrive.');
  await userEvent.click(screen.getByRole('button', { name: 'Send ticket' }));
  expect(await screen.findByRole('status')).toHaveTextContent('Saved as T-500001. The AI work is queued (job 1).');
  const headers = new Headers(fake.mock.calls[0][1]!.headers);
  expect(headers.get('Idempotency-Key')).toMatch(/^[0-9a-f-]{36}$/);
});
