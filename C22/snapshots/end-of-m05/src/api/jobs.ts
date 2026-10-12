// The background job of a new ticket (the queue of the scaling course): classify, draft, embed.
import { API_URL, apiFetch } from './client';

export const JOB_STATES = ['queued', 'running', 'succeeded', 'failed', 'cancelled', 'dead_letter'] as const;
export type JobState = (typeof JOB_STATES)[number];

export interface Job {
  job_id: number;
  ticket_id: string;
  state: JobState;
  attempts: number;
  max_attempts: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  last_error: string | null;
  result: { team: string; priority: number; draft_reply: string | null; embedding_version: string | null } | null;
}

/** A job in one of these states does not change any more by itself. */
export const isFinal = (s: JobState) => s === 'succeeded' || s === 'failed' || s === 'cancelled' || s === 'dead_letter';

export const getJob = (id: number, signal?: AbortSignal) => apiFetch<Job>(`/v1/jobs/${id}`, { signal });
export const cancelJob = (id: number) => apiFetch<Job>(`/v1/jobs/${id}/cancel`, { method: 'POST' });
export const retryJob = (id: number) => apiFetch<Job>(`/v1/jobs/${id}/retry`, { method: 'POST' });
export const jobEventsUrl = (id: number) => `${API_URL}/v1/jobs/${id}/events`;
