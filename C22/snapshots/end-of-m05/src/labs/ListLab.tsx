// A seeded problem: draw thousands of rows at once. Then the same rows with virtualization.
// It also shows the cost of downloading every ticket to show one screen of them.
import { useQuery } from '@tanstack/react-query';
import { useVirtualizer } from '@tanstack/react-virtual';
import { useLayoutEffect, useRef, useState } from 'react';
import { listTickets } from '../api/tickets';
import type { TicketSummary } from '../api/types';
import { TicketRow } from '../features/tickets/TicketRow';
import { afterNextPaint, ms } from './measure';

const SIZES = [100, 1000, 5000, 10000];

/** Downloads every ticket, page after page (the misconception: the screen shows about 11 of them). */
async function downloadAll(signal: AbortSignal) {
  const started = performance.now();
  const all: TicketSummary[] = [];
  let next: string | null = null;
  let requests = 0;
  do {
    const page = await listTickets({ status: '', team: '', q: '' }, 100, next, signal);
    all.push(...page.items);
    next = page.next;
    requests += 1;
  } while (next);
  return { tickets: all, requests, ms: performance.now() - started, bytes: JSON.stringify(all).length };
}

function PlainRows({ tickets }: { tickets: TicketSummary[] }) {
  return (
    <div className="scroller">
      <ul className="rows">
        {tickets.map((t) => (
          <li key={t.ticket_id}>
            <TicketRow ticket={t} selected={false} />
          </li>
        ))}
      </ul>
    </div>
  );
}

function VirtualRows({ tickets }: { tickets: TicketSummary[] }) {
  const scroller = useRef<HTMLDivElement>(null);
  const rows = useVirtualizer({ count: tickets.length, getScrollElement: () => scroller.current, estimateSize: () => 56, overscan: 8 });
  return (
    <div ref={scroller} className="scroller">
      <ul className="rows" style={{ height: rows.getTotalSize(), position: 'relative' }}>
        {rows.getVirtualItems().map((v) => (
          <li key={tickets[v.index].ticket_id} style={{ position: 'absolute', top: 0, left: 0, right: 0, transform: `translateY(${v.start}px)` }}>
            <TicketRow ticket={tickets[v.index]} selected={false} />
          </li>
        ))}
      </ul>
    </div>
  );
}

interface Run {
  n: number;
  mode: 'plain' | 'virtual';
  started: number;
  result: { ms: number; nodes: number } | null;
}

export function ListLab() {
  const all = useQuery({ queryKey: ['lab-all-tickets'], queryFn: ({ signal }) => downloadAll(signal), enabled: false, staleTime: Infinity });
  const [n, setN] = useState(1000);
  const [mode, setMode] = useState<Run['mode']>('plain');
  const [run, setRun] = useState<Run | null>(null);
  const box = useRef<HTMLDivElement>(null);

  // After React has put the rows in the page: wait for the paint, then measure.
  useLayoutEffect(() => {
    if (!run || run.result) return;
    void afterNextPaint().then((end) =>
      setRun({ ...run, result: { ms: end - run.started, nodes: box.current?.querySelectorAll('*').length ?? 0 } }),
    );
  }, [run]);

  const tickets = all.data?.tickets.slice(0, n) ?? [];
  return (
    <section className="card" aria-labelledby="list-lab-heading">
      <h2 id="list-lab-heading">Lab: thousands of rows</h2>
      <div className="toolbar">
        <button type="button" onClick={() => all.refetch()} disabled={all.isFetching}>
          {all.isFetching ? 'Downloading…' : 'Download every ticket'}
        </button>
        {all.data && (
          <span data-download-ms={all.data.ms.toFixed(1)} data-requests={all.data.requests}>
            {all.data.tickets.length} tickets in {all.data.requests} requests, {ms(all.data.ms)}, about{' '}
            {Math.round(all.data.bytes / 1024)} KB of JSON.
          </span>
        )}
      </div>
      <div className="toolbar">
        <label>
          Rows{' '}
          <select value={n} onChange={(e) => setN(Number(e.target.value))}>
            {SIZES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label>
          <input type="radio" name="mode" checked={mode === 'plain'} onChange={() => setMode('plain')} /> Every row
        </label>
        <label>
          <input type="radio" name="mode" checked={mode === 'virtual'} onChange={() => setMode('virtual')} /> Only the rows in view
        </label>
        <button type="button" disabled={!all.data} onClick={() => setRun({ n, mode, started: performance.now(), result: null })}>
          Draw
        </button>
        <button type="button" className="secondary" onClick={() => setRun(null)}>
          Clear
        </button>
      </div>
      {run?.result && (
        <p role="status" data-draw-ms={run.result.ms.toFixed(1)} data-dom-nodes={run.result.nodes}>
          {run.n} rows ({run.mode === 'plain' ? 'every row' : 'only the rows in view'}): on the screen after {ms(run.result.ms)};{' '}
          {run.result.nodes} elements in the page.
        </p>
      )}
      <div ref={box} key={run?.started}>
        {run && (run.mode === 'plain' ? <PlainRows tickets={tickets.slice(0, run.n)} /> : <VirtualRows tickets={tickets.slice(0, run.n)} />)}
      </div>
    </section>
  );
}
