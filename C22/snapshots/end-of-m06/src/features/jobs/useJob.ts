import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { cancelJob, getJob, isFinal, jobEventsUrl, retryJob, type Job } from '../../api/jobs';

export const jobKey = (id: number) => ['job', id] as const;

/** Polling: ask for the job every second until it is final. Simple, and it works everywhere. */
export function useJobPolling(id: number, intervalMs = 1000) {
  return useQuery({
    queryKey: jobKey(id),
    queryFn: ({ signal }) => getJob(id, signal),
    refetchInterval: (query) => (query.state.data && isFinal(query.state.data.state) ? false : intervalMs),
    staleTime: 0,
  });
}

/** Server-sent events: the server sends each new state; no repeated requests. */
export function useJobEvents(id: number): Job | null {
  const [job, setJob] = useState<Job | null>(null);
  useEffect(() => {
    const source = new EventSource(jobEventsUrl(id));
    source.addEventListener('state', (e) => {
      const next = JSON.parse((e as MessageEvent).data) as Job;
      setJob(next);
      if (isFinal(next.state)) source.close();
    });
    return () => source.close();
  }, [id]);
  return job;
}

export function useJobActions(id: number) {
  const client = useQueryClient();
  const done = (job: Job) => client.setQueryData(jobKey(id), job);
  return {
    cancel: useMutation({ mutationFn: () => cancelJob(id), onSuccess: done }),
    retry: useMutation({ mutationFn: () => retryJob(id), onSuccess: done }),
  };
}
