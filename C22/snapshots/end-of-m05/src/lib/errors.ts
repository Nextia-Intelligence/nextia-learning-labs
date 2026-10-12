// Errors in words that an agent understands, and whether trying again can help.
import { ApiError } from '../api/client';

export interface Described {
  text: string;
  canRetry: boolean;
}

const BY_CODE: Record<string, Described> = {
  network_error: { text: 'The ticket service did not answer. Check your connection, then try again.', canRetry: true },
  unavailable: { text: 'The ticket service is busy. Try again in a few seconds.', canRetry: true },
  ai_unavailable: { text: 'The AI service stopped answering. Your work is safe. Try again.', canRetry: true },
  no_draft: { text: 'No AI draft exists for this ticket. Write the reply yourself.', canRetry: false },
  not_found: { text: 'This item does not exist. It may have been removed.', canRetry: false },
  invalid_request: { text: 'Some information is not valid. Check the marked fields.', canRetry: false },
  conflict: { text: 'Someone or something changed this item first. Look at its new state.', canRetry: false },
  idempotency_key_reused: { text: 'This form was already sent with other content. Reload the page.', canRetry: false },
};

export function describeError(error: Error): Described {
  if (error instanceof ApiError) {
    const known = BY_CODE[error.code];
    if (known) {
      if (error.retryAfter) return { ...known, text: known.text.replace('a few seconds', `${error.retryAfter} seconds`) };
      return known;
    }
    return { text: error.message, canRetry: error.status >= 500 };
  }
  return { text: 'Something went wrong in this page. Reload it to try again.', canRetry: false };
}
