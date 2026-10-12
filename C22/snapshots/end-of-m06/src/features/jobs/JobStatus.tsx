import type { JobState } from '../../api/jobs';
import { ErrorMessage } from '../../ui/ErrorMessage';
import { useJobActions, useJobPolling } from './useJob';

const STEPS: { state: JobState; label: string }[] = [
  { state: 'queued', label: 'Waiting' },
  { state: 'running', label: 'Working' },
  { state: 'succeeded', label: 'Done' },
];

const TEXT: Record<JobState, string> = {
  queued: 'The AI work waits in the queue.',
  running: 'The AI is working on the ticket: team, priority and a first draft.',
  succeeded: 'The AI work is done.',
  failed: 'The AI work failed. Trying again will not help; a person must sort the ticket.',
  cancelled: 'You cancelled the AI work. The ticket is saved without it.',
  dead_letter: 'The AI work failed several times and stopped. You can try again later.',
};

/** The state of one background job, asked for every second (polling) until it is final. */
export function JobStatus({ jobId, estimatedSeconds }: { jobId: number; estimatedSeconds?: number }) {
  const job = useJobPolling(jobId);
  const { cancel, retry } = useJobActions(jobId);

  if (job.isPending) return <p className="muted">Checking the AI work…</p>;
  if (job.isError) return <ErrorMessage error={job.error} onRetry={() => job.refetch()} />;
  const j = job.data;
  const current = j.state === 'failed' || j.state === 'dead_letter' ? 'running' : j.state;
  const bad = j.state === 'failed' || j.state === 'dead_letter';
  return (
    <section aria-labelledby="job-heading" data-state={j.state}>
      <h3 id="job-heading">AI work for {j.ticket_id}</h3>
      <ol className="steps" aria-label="Progress">
        {STEPS.map((s) => (
          <li key={s.state} aria-current={s.state === current ? 'step' : undefined}>
            {s.label}
          </li>
        ))}
      </ol>
      <p role="status" className={bad ? 'error' : j.state === 'succeeded' ? 'success' : undefined}>
        {TEXT[j.state]}
        {j.state === 'queued' && estimatedSeconds ? ` About ${Math.ceil(estimatedSeconds)} seconds.` : ''}
      </p>
      {j.last_error && <p className="muted">Details: {j.last_error}</p>}
      {j.result && (
        <p>
          Team: <strong>{j.result.team}</strong>, priority {j.result.priority}.
        </p>
      )}
      <div className="toolbar">
        {j.state === 'queued' && (
          <button type="button" className="secondary" onClick={() => cancel.mutate()} disabled={cancel.isPending}>
            Cancel the AI work
          </button>
        )}
        {j.state === 'dead_letter' && (
          <button type="button" onClick={() => retry.mutate()} disabled={retry.isPending}>
            Try again
          </button>
        )}
      </div>
      {(cancel.error ?? retry.error) && <ErrorMessage error={(cancel.error ?? retry.error)!} />}
    </section>
  );
}
