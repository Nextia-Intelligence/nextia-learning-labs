import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeAll, expect, test } from 'vitest';
import { apiError, installFakeApi, json, ticket } from '../../test/fakeApi';
import { renderWithCache } from '../../test/render';
import { TicketList } from './TicketList';

// jsdom does not lay out the page, so every element is 0 px high. The virtual list needs the
// height of its scroll box to know how many rows to draw: give every element 600 × 800 px.
beforeAll(() => {
  Object.defineProperty(HTMLElement.prototype, 'offsetHeight', { configurable: true, get: () => 600 });
  Object.defineProperty(HTMLElement.prototype, 'offsetWidth', { configurable: true, get: () => 800 });
});

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

test('loads the next page with the cursor of the last one when the end is in view', async () => {
  const fake = installFakeApi((url) =>
    url.searchParams.get('after') === 'page-2'
      ? json(200, { items: [ticket(3)], next: null })
      : json(200, { items: [ticket(1), ticket(2)], next: 'page-2' }),
  );
  renderWithCache(<TicketList selectedId={null} />);
  expect(await screen.findByText('Ticket number 3')).toBeInTheDocument();
  expect(screen.getByText(/Showing 3 tickets\./)).toBeInTheDocument();
  expect(fake).toHaveBeenCalledTimes(2);
  expect(new URL(String(fake.mock.calls[1][0])).searchParams.get('after')).toBe('page-2');
});

test('shows a busy server in plain words and can try again', async () => {
  let calls = 0;
  installFakeApi(() => (++calls === 1 ? apiError(503, 'unavailable', 'The ticket service is not available.') : json(200, { items: [ticket(1)], next: null })));
  renderWithCache(<TicketList selectedId={null} />);
  expect(await screen.findByRole('alert')).toHaveTextContent('The ticket service is busy.');
  await userEvent.click(screen.getByRole('button', { name: 'Try again' }));
  expect(await screen.findByText('Ticket number 1')).toBeInTheDocument();
});

test('draws only the rows in view, not every loaded ticket', async () => {
  const items = Array.from({ length: 50 }, (_, i) => ticket(i + 1));
  installFakeApi(() => json(200, { items, next: null }));
  renderWithCache(<TicketList selectedId={null} />);
  expect(await screen.findByText('Showing 50 tickets.')).toBeInTheDocument();
  const drawn = screen.getAllByRole('link').length;
  expect(drawn).toBeGreaterThan(5);
  expect(drawn).toBeLessThan(25); // 600 px ÷ 56 px ≈ 11 rows, plus 8 above and below
});
