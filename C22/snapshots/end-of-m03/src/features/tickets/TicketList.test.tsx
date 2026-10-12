import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test } from 'vitest';
import { apiError, installFakeApi, json, ticket } from '../../test/fakeApi';
import { renderWithCache } from '../../test/render';
import { TicketList } from './TicketList';

test('shows the tickets of the first page', async () => {
  installFakeApi(() => json(200, { items: [ticket(1), ticket(2, { status: 'pending' })], next: null }));
  renderWithCache(<TicketList selectedId={null} />);
  expect(await screen.findByText('Ticket number 1')).toBeInTheDocument();
  expect(screen.getByText('Pending')).toBeInTheDocument();
});

test('sends the search to the server', async () => {
  const fake = installFakeApi(() => json(200, { items: [], next: null }));
  renderWithCache(<TicketList selectedId={null} />);
  await userEvent.type(screen.getByRole('searchbox', { name: 'Search' }), 'hose');
  expect(await screen.findByText('No ticket matches.')).toBeInTheDocument();
  const last = new URL(String(fake.mock.calls.at(-1)![0]));
  expect(last.searchParams.get('q')).toBe('hose');
});

test('loads the next page with the cursor of the last one', async () => {
  const fake = installFakeApi((url) =>
    url.searchParams.get('after') === 'page-2'
      ? json(200, { items: [ticket(3)], next: null })
      : json(200, { items: [ticket(1), ticket(2)], next: 'page-2' }),
  );
  renderWithCache(<TicketList selectedId={null} />);
  await userEvent.click(await screen.findByRole('button', { name: 'Load 50 more' }));
  expect(await screen.findByText('Ticket number 3')).toBeInTheDocument();
  expect(screen.getByText(/Showing 3 tickets\./)).toBeInTheDocument();
  expect(fake).toHaveBeenCalledTimes(2);
});

test('shows the API’s error and can try again', async () => {
  let calls = 0;
  installFakeApi(() => (++calls === 1 ? apiError(503, 'unavailable', 'The ticket service is not available.') : json(200, { items: [ticket(1)], next: null })));
  renderWithCache(<TicketList selectedId={null} />);
  expect(await screen.findByRole('alert')).toHaveTextContent('The ticket service is not available.');
  await userEvent.click(screen.getByRole('button', { name: 'Try again' }));
  expect(await screen.findByText('Ticket number 1')).toBeInTheDocument();
});
