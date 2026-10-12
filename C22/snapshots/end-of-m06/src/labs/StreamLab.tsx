// What does it cost to draw the draft again for every piece of text? The same recorded stream,
// drawn for every piece or once per frame (the pieces that arrived during one frame together).
import { Profiler, useRef, useState, type ProfilerOnRenderCallback } from 'react';
import { streamDraft } from '../api/drafts';
import { afterNextPaint, ms } from './measure';

type Mode = 'every' | 'frame';
interface Result {
  firstTextMs: number;
  totalMs: number;
  pieces: number;
  commits: number;
  renderMs: number;
}

export function StreamLab() {
  const [ticketId, setTicketId] = useState('T-64704');
  const [mode, setMode] = useState<Mode>('every');
  const [text, setText] = useState('');
  const [result, setResult] = useState<Result | null>(null);
  const [running, setRunning] = useState(false);
  const stats = useRef({ commits: 0, renderMs: 0 });
  const onRender: ProfilerOnRenderCallback = (_id, _phase, actual) => {
    stats.current.commits += 1;
    stats.current.renderMs += actual;
  };

  async function run() {
    setText('');
    setResult(null);
    setRunning(true);
    await afterNextPaint();
    stats.current = { commits: 0, renderMs: 0 };
    const started = performance.now();
    let firstTextMs = 0;
    let pieces = 0;
    let pending = '';
    let frame = 0;
    const flush = () => {
      frame = 0;
      const add = pending;
      pending = '';
      setText((t) => t + add);
    };
    await streamDraft(
      ticketId,
      (e) => {
        if (e.type !== 'token') return;
        pieces += 1;
        if (pieces === 1) void afterNextPaint().then((t) => (firstTextMs = t - started));
        if (mode === 'every') setText((t) => t + e.text);
        else {
          pending += e.text;
          if (!frame) frame = requestAnimationFrame(flush);
        }
      },
      new AbortController().signal,
    );
    if (frame) {
      cancelAnimationFrame(frame);
      flush();
    }
    const end = await afterNextPaint();
    setRunning(false);
    setResult({ firstTextMs, totalMs: end - started, pieces, ...stats.current });
  }

  return (
    <section className="card" aria-labelledby="stream-lab-heading">
      <h2 id="stream-lab-heading">Lab: draw every piece of a stream?</h2>
      <div className="toolbar">
        <label>
          Ticket <input value={ticketId} onChange={(e) => setTicketId(e.target.value)} size={9} />
        </label>
        <label>
          <input type="radio" name="draw" checked={mode === 'every'} onChange={() => setMode('every')} /> For every piece
        </label>
        <label>
          <input type="radio" name="draw" checked={mode === 'frame'} onChange={() => setMode('frame')} /> Once per frame
        </label>
        <button type="button" onClick={run} disabled={running}>
          Stream the draft
        </button>
      </div>
      {result && (
        <p
          role="status"
          data-first-text-ms={result.firstTextMs.toFixed(1)}
          data-total-ms={result.totalMs.toFixed(1)}
          data-pieces={result.pieces}
          data-commits={result.commits}
          data-render-ms={result.renderMs.toFixed(2)}
        >
          First text after {ms(result.firstTextMs)}; finished after {ms(result.totalMs)}. {result.pieces} pieces,{' '}
          {result.commits} React updates, {ms(result.renderMs)} in React.
        </p>
      )}
      <Profiler id="stream-lab" onRender={onRender}>
        <div className="draft-text">{text}</div>
      </Profiler>
    </section>
  );
}
