// A very small router: the part of the address after # says which page to show.
//   #/tickets            the ticket list
//   #/tickets/T-80008    the list and one ticket
//   #/new                the form for a new ticket
import { useSyncExternalStore } from 'react';

export type Route =
  | { page: 'tickets'; ticketId: string | null }
  | { page: 'new' }
  | { page: 'labs'; lab: string | null };

export function parseRoute(hash: string): Route {
  const parts = hash.replace(/^#\/?/, '').split('/').filter(Boolean);
  if (parts[0] === 'new') return { page: 'new' };
  if (parts[0] === 'labs') return { page: 'labs', lab: parts[1] ?? null };
  return { page: 'tickets', ticketId: parts[0] === 'tickets' && parts[1] ? parts[1] : null };
}

const subscribe = (onChange: () => void) => {
  window.addEventListener('hashchange', onChange);
  return () => window.removeEventListener('hashchange', onChange);
};

/** The current route; the component draws again when the address changes. */
export function useRoute(): Route {
  const hash = useSyncExternalStore(subscribe, () => window.location.hash);
  return parseRoute(hash);
}
