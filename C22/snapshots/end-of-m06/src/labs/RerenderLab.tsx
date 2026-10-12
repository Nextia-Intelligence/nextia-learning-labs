// How often does React draw the rows again? Type in the note above 50 rows and count.
//   state too high: the note's text is state of the component that also draws the rows;
//   memo: the same, with every row wrapped in memo (the shortcut "memoize everything");
//   state moved down: the note keeps its own text; the rows do not see it.
import { useQuery } from '@tanstack/react-query';
import { memo, Profiler, useRef, useState, type ProfilerOnRenderCallback } from 'react';
import { listTickets } from '../api/tickets';
import type { TicketSummary } from '../api/types';
import { TicketRow } from '../features/tickets/TicketRow';

type Variant = 'high' | 'memo' | 'moved';
const counts = { rowRenders: 0, commits: 0, renderMs: 0 };

function CountedRow({ ticket }: { ticket: TicketSummary }) {
  counts.rowRenders += 1;
  return <TicketRow ticket={ticket} selected={false} />;
}
const MemoRow = memo(CountedRow);

function Rows({ tickets, memoized }: { tickets: TicketSummary[]; memoized: boolean }) {
  const Row = memoized ? MemoRow : CountedRow;
  return (
    <ul className="rows">
      {tickets.map((t) => (
        <li key={t.ticket_id}>
          <Row ticket={t} />
        </li>
      ))}
    </ul>
  );
}

function NoteBox() {
  const [note, setNote] = useState('');
  return (
    <label className="form">
      Note for the team
      <input value={note} onChange={(e) => setNote(e.target.value)} />
    </label>
  );
}

function StateTooHigh({ tickets, memoized }: { tickets: TicketSummary[]; memoized: boolean }) {
  const [note, setNote] = useState('');
  return (
    <>
      <label className="form">
        Note for the team
        <input value={note} onChange={(e) => setNote(e.target.value)} />
      </label>
      <Rows tickets={tickets} memoized={memoized} />
    </>
  );
}

function StateMovedDown({ tickets }: { tickets: TicketSummary[] }) {
  return (
    <>
      <NoteBox />
      <Rows tickets={tickets} memoized={false} />
    </>
  );
}

export function RerenderLab() {
  const page = useQuery({ queryKey: ['lab-rerender'], queryFn: ({ signal }) => listTickets({ status: '', team: '', q: '' }, 50, null, signal) });
  const [variant, setVariant] = useState<Variant>('high');
  const status = useRef<HTMLSpanElement>(null);
  // The counts are written straight into the page, not into React state: showing them must not
  // make React draw the rows again.
  const show = () => {
    const el = status.current;
    if (!el) return;
    el.textContent = `Rows drawn: ${counts.rowRenders} · React updates: ${counts.commits} · time in React: ${counts.renderMs.toFixed(1)} ms`;
    el.dataset.rowRenders = String(counts.rowRenders);
    el.dataset.commits = String(counts.commits);
    el.dataset.renderMs = counts.renderMs.toFixed(2);
  };
  const onRender: ProfilerOnRenderCallback = (_id, _phase, actual) => {
    counts.commits += 1;
    counts.renderMs += actual;
    queueMicrotask(show);
  };
  const reset = () => {
    Object.assign(counts, { rowRenders: 0, commits: 0, renderMs: 0 });
    show();
  };
  const tickets = page.data?.items ?? [];
  return (
    <section className="card" aria-labelledby="rerender-heading">
      <h2 id="rerender-heading">Lab: rows drawn again</h2>
      <fieldset className="toolbar">
        <legend>Where the note’s text lives</legend>
        {(['high', 'memo', 'moved'] as const).map((v) => (
          <label key={v}>
            <input type="radio" name="where" checked={variant === v} onChange={() => setVariant(v)} />{' '}
            {{ high: 'State too high', memo: 'State too high, rows in memo', moved: 'State moved down' }[v]}
          </label>
        ))}
      </fieldset>
      <div className="toolbar">
        <button type="button" className="secondary" onClick={reset}>
          Reset the counts
        </button>
        <span ref={status} aria-live="off" data-row-renders="0" data-commits="0" data-render-ms="0">
          Rows drawn: 0
        </span>
      </div>
      <Profiler id="rerender-lab" onRender={onRender}>
        {tickets.length > 0 &&
          (variant === 'moved' ? (
            <StateMovedDown key={variant} tickets={tickets} />
          ) : (
            <StateTooHigh key={variant} tickets={tickets} memoized={variant === 'memo'} />
          ))}
      </Profiler>
    </section>
  );
}
