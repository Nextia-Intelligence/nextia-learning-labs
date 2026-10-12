import { expect, test } from 'vitest';
import { SseParser } from './sse';

test('reads complete events and keeps a half event for later', () => {
  const p = new SseParser();
  expect(p.push('event: token\ndata: {"text":"Hel')).toEqual([]);
  expect(p.push('lo"}\n\nevent: token\ndata: {"text":" there"}\n\n')).toEqual([
    { event: 'token', data: '{"text":"Hello"}' },
    { event: 'token', data: '{"text":" there"}' },
  ]);
});

test('accepts Windows line ends and joins several data lines', () => {
  expect(new SseParser().push('data: a\r\ndata: b\r\n\r\n')).toEqual([{ event: 'message', data: 'a\nb' }]);
});
