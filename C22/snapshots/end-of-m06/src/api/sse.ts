// Reads server-sent events (SSE) from text that arrives in pieces. A piece of the network can end
// in the middle of an event, so the parser keeps the unfinished part until the rest arrives.

export interface SseEvent {
  event: string;
  data: string;
}

export class SseParser {
  private buffer = '';

  /** Adds the next piece of text; gives back the events that are now complete. */
  push(text: string): SseEvent[] {
    this.buffer += text.replace(/\r\n?/g, '\n');
    const events: SseEvent[] = [];
    let end: number;
    while ((end = this.buffer.indexOf('\n\n')) !== -1) {
      const block = this.buffer.slice(0, end);
      this.buffer = this.buffer.slice(end + 2);
      let event = 'message';
      const data: string[] = [];
      for (const line of block.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim();
        else if (line.startsWith('data:')) data.push(line.slice(5).replace(/^ /, ''));
      }
      if (data.length) events.push({ event, data: data.join('\n') });
    }
    return events;
  }
}
