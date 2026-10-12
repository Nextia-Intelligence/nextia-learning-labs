import { act, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test } from 'vitest';
import { deferred, installFakeApi, json, ticket } from '../test/fakeApi';
import { renderWithCache } from '../test/render';
import { RaceLab } from './RaceLab';

/** "p" answers last. Gives back a function that sends the two answers in that order. */
function slowFirstSearch() {
  const answers = new Map<string, ReturnType<typeof deferred<Response>>>();
  installFakeApi((url) => {
    const q = url.searchParams.get('q') ?? '';
    if (!answers.has(q)) answers.set(q, deferred<Response>());
    return answers.get(q)!.promise;
  });
  return async () => {
    await act(async () => answers.get('pa')!.resolve(json(200, { items: [ticket(2)], next: null })));
    await act(async () => answers.get('p')?.resolve(json(200, { items: [ticket(1), ticket(3)], next: null })));
  };
}

test('without cleanup, the old answer replaces the new one (the mistake)', async () => {
  const answerInOrder = slowFirstSearch();
  renderWithCache(<RaceLab />);
  await userEvent.type(screen.getByRole('searchbox'), 'pa');
  await answerInOrder();
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Results for “p”'));
});

test.each(['Effect with cleanup', 'TanStack Query'])('%s shows the answer for what the box says', async (name) => {
  const answerInOrder = slowFirstSearch();
  renderWithCache(<RaceLab />);
  await userEvent.click(screen.getByLabelText(name));
  await userEvent.type(screen.getByRole('searchbox'), 'pa');
  await answerInOrder();
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Results for “pa”'));
});
