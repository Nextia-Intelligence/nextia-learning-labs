// The main task, by keyboard only: find a ticket, write a draft, use it, send the reply; then a
// new ticket and its background job. Runs on a desktop screen and on a phone screen.
import { expect, test } from '@playwright/test';

test.beforeEach(async ({ request }) => {
  const api = `http://127.0.0.1:${process.env.E2E_API_PORT ?? 8100}`;
  await request.post(`${api}/admin/reset`);
});

test('answer a ticket with the AI draft, by keyboard only', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText(/Showing \d+ tickets/)).toBeVisible();

  // Skip link, then the search box: Tab moves the focus, the keyboard types.
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to the main content' })).toBeFocused();
  await page.getByRole('searchbox', { name: 'Search' }).focus();
  await page.keyboard.type('garden shed');
  const row = page.getByRole('link', { name: /T-80008/ });
  await expect(row).toBeVisible();
  await row.focus();
  await page.keyboard.press('Enter');

  // The focus moves to the ticket's heading.
  await expect(page.getByRole('heading', { level: 2, name: /where is my order LK-581106/i })).toBeFocused();

  // Write a draft with the keyboard; the focus stays on the same button.
  const write = page.getByRole('button', { name: 'Write a draft' });
  await write.focus();
  await page.keyboard.press('Enter');
  const status = page.locator('.draft [role="status"]');
  await expect(status).toHaveText('Draft finished. No sources.', { timeout: 15_000 });
  await expect(page.getByRole('button', { name: 'Write a new draft' })).toBeFocused();

  // The accessibility tree of the draft: what a screen reader user gets.
  await expect(page.locator('.draft')).toMatchAriaSnapshot(`
    - heading "AI draft" [level=3]
    - status: Draft finished. No sources.
    - button "Write a new draft"
    - button "Use this draft"
    - button "Discard"
  `);

  await page.getByRole('button', { name: 'Use this draft' }).focus();
  await page.keyboard.press('Enter');
  const reply = page.getByLabel('Reply to the customer');
  await expect(reply).toHaveValue(/garden shed/);
  await page.getByRole('button', { name: 'Send reply' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByText('Sent.')).toBeVisible();
  await expect(page.locator('.message-agent').last()).toContainText('garden shed');
});

test('send a new ticket and follow its background job', async ({ page }) => {
  await page.goto('/#/new');
  await page.getByLabel('Customer ID').focus();
  await page.keyboard.type('C-0022');
  await page.keyboard.press('Tab');
  await page.keyboard.type('Parcel lost');
  await page.keyboard.press('Tab');
  await page.keyboard.type('My parcel did not arrive.');
  await page.keyboard.press('Tab');
  await page.keyboard.press('Enter');
  await expect(page.getByText(/Saved as T-500001/)).toBeFocused();
  await expect(page.getByText('The AI work is done.')).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText(/Team: shipping/)).toBeVisible();
});

test('a slow, failing list says so in words and recovers', async ({ page, request }) => {
  const api = `http://127.0.0.1:${process.env.E2E_API_PORT ?? 8100}`;
  await request.post(`${api}/admin/mode`, { data: { list: 'fail' } });
  await page.goto('/');
  await expect(page.getByRole('alert')).toContainText('The ticket service is busy', { timeout: 15_000 });
  await request.post(`${api}/admin/mode`, { data: { list: 'normal' } });
  await page.getByRole('button', { name: 'Try again' }).click();
  await expect(page.getByText(/Showing \d+ tickets/)).toBeVisible();
});
