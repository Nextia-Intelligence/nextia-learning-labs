import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test } from 'vitest';
import { installFakeApi, json, ticket } from '../test/fakeApi';
import { renderWithCache } from '../test/render';
import { RerenderLab } from './RerenderLab';

async function rowsDrawnWhileTyping(variant: string) {
  installFakeApi(() => json(200, { items: Array.from({ length: 50 }, (_, i) => ticket(i + 1)), next: null }));
  renderWithCache(<RerenderLab />);
  await screen.findByText('Ticket number 1');
  await userEvent.click(screen.getByLabelText(variant));
  await screen.findByText('Ticket number 1');
  await userEvent.click(screen.getByRole('button', { name: 'Reset the counts' }));
  await userEvent.type(screen.getByLabelText('Note for the team'), 'hello');
  const status = screen.getByText(/Rows drawn:/);
  await waitFor(() => expect(Number(status.dataset.commits)).toBeGreaterThan(0));
  return Number(status.dataset.rowRenders);
}

test('with the state too high, every key draws the 50 rows again', async () => {
  expect(await rowsDrawnWhileTyping('State too high')).toBe(5 * 50);
});

test('with the state moved down, typing draws no row again', async () => {
  expect(await rowsDrawnWhileTyping('State moved down')).toBe(0);
});
