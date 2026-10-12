import { expect, test } from 'vitest';
import { renderMarkdown } from './markdown';

test('keeps the formatting of the draft', () => {
  const html = renderMarkdown('1. **We check your order**\n2. You get an email.');
  expect(html).toContain('<strong>We check your order</strong>');
  expect(html).toContain('<ol>');
});

test('removes HTML that runs code: an image with onerror, a script, a javascript: link', () => {
  const html = renderMarkdown(
    'Hi <img src=x onerror="alert(1)"> <script>alert(2)</script> [click](javascript:alert(3)) <a href="https://example.com/returns">policy</a>',
  );
  expect(html).not.toMatch(/onerror|<script|<img|javascript:/i);
  expect(html).toContain('href="https://example.com/returns"');
  expect(html).toContain('rel="noopener noreferrer"');
});
