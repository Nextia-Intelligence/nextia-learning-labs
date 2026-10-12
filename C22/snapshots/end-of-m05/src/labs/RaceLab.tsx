// The stale-response problem, on purpose. Type "parcel" one letter at a time: the search "p"
// matches many tickets, so its answer is slow and arrives last. Which results stay on the screen?
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { listTickets } from '../api/tickets';
import type { TicketPage } from '../api/types';
import { useApi } from '../lib/useApi';

type Variant = 'naive' | 'cleanup' | 'library';
interface Answer {
  q: string;
  page: TicketPage;
}

const search = (q: string, signal?: AbortSignal) =>
  listTickets({ status: '', team: '', q }, 20, null, signal).then((page): Answer => ({ q, page }));

/** The mistake: an effect without cleanup. Every answer is shown when it arrives, also an old one. */
function useNaiveSearch(q: string): Answer | null {
  const [answer, setAnswer] = useState<Answer | null>(null);
  useEffect(() => {
    search(q).then(setAnswer, () => {});
  }, [q]);
  return answer;
}

function useCleanupSearch(q: string): Answer | null {
  return useApi((signal) => search(q, signal), [q]).data;
}

function useLibrarySearch(q: string): Answer | null {
  return useQuery({ queryKey: ['race', q], queryFn: ({ signal }) => search(q, signal) }).data ?? null;
}

function Results({ q, variant }: { q: string; variant: Variant }) {
  const use = { naive: useNaiveSearch, cleanup: useCleanupSearch, library: useLibrarySearch }[variant];
  const answer = use(q);
  const wrong = answer !== null && answer.q !== q;
  return (
    <div data-results-for={answer?.q ?? ''} data-typed={q}>
      <p className={wrong ? 'error' : 'muted'} role="status">
        {answer === null
          ? 'No answer yet.'
          : `Results for “${answer.q}”: ${answer.page.items.length} tickets${wrong ? ` — but the box says “${q}”` : ''}.`}
      </p>
      <ul>
        {answer?.page.items.slice(0, 5).map((t) => (
          <li key={t.ticket_id}>
            {t.ticket_id}: {t.subject}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function RaceLab() {
  const [q, setQ] = useState('');
  const [variant, setVariant] = useState<Variant>('naive');
  return (
    <section className="card" aria-labelledby="race-heading">
      <h2 id="race-heading">Lab: an old answer arrives last</h2>
      <fieldset className="toolbar">
        <legend>How the search loads its results</legend>
        {(['naive', 'cleanup', 'library'] as const).map((v) => (
          <label key={v}>
            <input type="radio" name="variant" value={v} checked={variant === v} onChange={() => setVariant(v)} />{' '}
            {{ naive: 'Effect without cleanup', cleanup: 'Effect with cleanup', library: 'TanStack Query' }[v]}
          </label>
        ))}
      </fieldset>
      <label className="form">
        Search
        <input type="search" value={q} onChange={(e) => setQ(e.target.value)} />
      </label>
      <Results key={variant} q={q} variant={variant} />
    </section>
  );
}
