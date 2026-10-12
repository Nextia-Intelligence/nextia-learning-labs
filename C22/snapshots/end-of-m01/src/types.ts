// The ticket API's data, as TypeScript types (from the API's contract).
// TypeScript checks these before the code runs: a typing mistake in a field name is an error.

export interface TicketSummary {
  ticket_id: string;
  customer_id: string;
  customer_name: string;
  subject: string;
  team: string;
  priority: number;
  status: string;
  created_at: string;
}

export interface TicketPage {
  items: TicketSummary[];
  next: string | null;
}

export interface NewTicket {
  customer_id: string;
  subject: string;
  body: string;
}

export interface TicketAccepted {
  ticket_id: string;
  job_id: number;
  state: string;
}

/** The API's error shape: {"error": {"code", "message", "request_id", "fields"}}. */
export interface ApiErrorBody {
  error: { code: string; message: string; request_id: string; fields: string[] };
}
