// Polling or server-sent events? One new ticket; two ways to follow its job. Count the requests.
import { useQuery } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { getJob, isFinal } from '../api/jobs';
import { createTicket } from '../api/tickets';
import { useJobEvents } from '../features/jobs/useJob';

function Polling({ jobId }: { jobId: number }) {
  const requests = useRef(0);
  const job = useQuery({
    queryKey: ['lab-job', jobId],
    queryFn: ({ signal }) => {
      requests.current += 1;
      return getJob(jobId, signal);
    },
    refetchInterval: (q) => (q.state.data && isFinal(q.state.data.state) ? false : 1000),
    staleTime: 0,
  });
  return (
    <div data-transport="polling" data-state={job.data?.state ?? ''}>
      <h3>Polling (a request every second)</h3>
      <p>State: {job.data?.state ?? '…'}</p>
      <p>Requests: {requests.current}</p>
    </div>
  );
}

function Events({ jobId }: { jobId: number }) {
  const job = useJobEvents(jobId);
  const [events, setEvents] = useState(0);
  useEffect(() => {
    if (job) setEvents((n) => n + 1);
  }, [job]);
  return (
    <div data-transport="sse" data-state={job?.state ?? ''}>
      <h3>Server-sent events (one open connection)</h3>
      <p>State: {job?.state ?? '…'}</p>
      <p>Requests: 1 · events received: {events}</p>
    </div>
  );
}

export function JobLab() {
  const [jobId, setJobId] = useState<number | null>(null);
  async function send() {
    const answer = await createTicket({ customer_id: 'C-0022', subject: 'Lab: parcel lost', body: 'My parcel did not arrive.' });
    setJobId(answer.job_id);
  }
  return (
    <section className="card" aria-labelledby="job-lab-heading">
      <h2 id="job-lab-heading">Lab: follow a background job</h2>
      <button type="button" onClick={send}>
        Send a test ticket
      </button>
      {jobId !== null && (
        <div className="layout" key={jobId}>
          <Polling jobId={jobId} />
          <Events jobId={jobId} />
        </div>
      )}
    </section>
  );
}
