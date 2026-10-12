// The ticket requests. Each function takes an AbortSignal where a request can be cancelled.
import { apiFetch } from './client';
import type { Message, NewTicket, Status, TicketAccepted, TicketDetail, TicketFilter, TicketPage } from './types';

/** The query string of the list: only the filters that are set. */
export function listQuery(filter: TicketFilter, limit: number, after?: string | null): string {
  const p = new URLSearchParams({ limit: String(limit) });
  if (filter.status) p.set('status', filter.status);
  if (filter.team) p.set('team', filter.team);
  if (filter.q.trim()) p.set('q', filter.q.trim());
  if (after) p.set('after', after);
  return p.toString();
}

export function listTickets(filter: TicketFilter, limit: number, after?: string | null, signal?: AbortSignal) {
  return apiFetch<TicketPage>(`/v1/tickets?${listQuery(filter, limit, after)}`, { signal });
}

export function getTicket(id: string, signal?: AbortSignal) {
  return apiFetch<TicketDetail>(`/v1/tickets/${id}`, { signal });
}

export function createTicket(ticket: NewTicket, idempotencyKey?: string) {
  return apiFetch<TicketAccepted>('/v1/tickets', {
    method: 'POST',
    body: JSON.stringify(ticket),
    headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {},
  });
}

export function addMessage(id: string, body: string) {
  return apiFetch<Message>(`/v1/tickets/${id}/messages`, {
    method: 'POST',
    body: JSON.stringify({ author: 'agent', body }),
  });
}

export function setStatus(id: string, status: Status) {
  return apiFetch<TicketDetail>(`/v1/tickets/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) });
}
