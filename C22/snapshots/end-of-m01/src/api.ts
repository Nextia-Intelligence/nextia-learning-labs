// The requests to the ticket API. The page and the API are on different addresses now
// (Vite on localhost:5173, the API on 127.0.0.1:8100), so every request uses the full address,
// and the API must allow this page's origin (CORS).
import type { ApiErrorBody, NewTicket, TicketAccepted, TicketPage, TicketSummary } from './types';

export const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8100';

/** Reads one page of tickets from the API. */
export async function loadTickets(limit: number): Promise<TicketSummary[]> {
  const response = await fetch(`${API_URL}/v1/tickets?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`The API answered ${response.status}`);
  }
  const page = (await response.json()) as TicketPage;
  return page.items;
}

/** Sends a new ticket. The answer is the saved ticket, or the API's error in words. */
export async function sendTicket(ticket: NewTicket): Promise<TicketAccepted | string> {
  const response = await fetch(`${API_URL}/v1/tickets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(ticket),
  });
  const body = await response.json();
  if (response.ok) return body as TicketAccepted;
  const { error } = body as ApiErrorBody;
  return `Not saved: ${error.message} Fields: ${error.fields.join(', ')}`;
}

/** The text of one ticket in the list. */
export function ticketLine(ticket: TicketSummary): string {
  return `${ticket.ticket_id}: ${ticket.subject} (${ticket.customer_name} · ${ticket.team} · ${ticket.status})`;
}
