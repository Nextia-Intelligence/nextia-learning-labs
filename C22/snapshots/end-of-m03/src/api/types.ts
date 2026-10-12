// The ticket API's data, as TypeScript types (from the API's contract).

export const TEAMS = ['billing', 'login', 'shipping', 'account', 'other'] as const;
export const STATUSES = ['open', 'pending', 'resolved', 'closed'] as const;
export type Team = (typeof TEAMS)[number];
export type Status = (typeof STATUSES)[number];

export interface TicketSummary {
  ticket_id: string;
  customer_id: string;
  customer_name: string;
  subject: string;
  team: Team;
  priority: number;
  status: Status;
  created_at: string;
  message_count: number;
  last_message_at: string | null;
}

export interface TicketPage {
  items: TicketSummary[];
  next: string | null;
}

export interface Message {
  message_id: number;
  author: 'customer' | 'agent';
  body: string;
  created_at: string;
}

export interface TicketDetail extends Omit<TicketSummary, 'last_message_at'> {
  body: string;
  channel: string;
  updated_at: string;
  messages: Message[];
  has_draft: boolean;
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
  status_url: string;
  queued_ahead: number;
  estimated_wait_seconds: number;
}

export interface TicketFilter {
  status: Status | '';
  team: Team | '';
  q: string;
}
