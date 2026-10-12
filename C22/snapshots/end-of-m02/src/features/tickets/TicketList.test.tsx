import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test } from 'vitest';
import { apiError, installFakeApi, json, ticket } from '../../test/fakeApi';
import { TicketList } from './TicketList';

test('shows the tickets of the first page', async () => {
  installFakeApi(() => json(200, { items: [ticket(1), ticket(2, { status: 'pending' })], next: null }));
  render(<TicketList selectedId={null} />);
  expect(await screen.findByText('Ticket number 1')).toBeInTheDocument();
  expect(screen.getByText('Pending')).toBeInTheDocument();
});

test('sends the search to the server', async () => {
  const fake = installFakeApi(() => json(200, { items: [], next: null }));
  render(<TicketList selectedId={null} />);
  await userEvent.type(screen.getByRole('searchbox', { name: 'Search' }), 'hose');
  expect(await screen.findByText('No ticket matches.')).toBeInTheDocument();
  const last = new URL(String(fake.mock.calls.at(-1)![0]));
  expect(last.searchParams.get('q')).toBe('hose');
});

test('shows the API’s error message', async () => {
  installFakeApi(() => apiError(503, 'unavailable', 'The ticket service is not available.'));
  render(<TicketList selectedId={null} />);
  expect(await screen.findByRole('alert')).toHaveTextContent('The ticket service is not available.');
});
