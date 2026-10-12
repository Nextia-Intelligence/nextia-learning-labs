import { lazy, Suspense } from 'react';
import { TicketList } from './features/tickets/TicketList';
import { TicketView } from './features/tickets/TicketView';
import { useRoute } from './router';

// Loaded only when the agent opens them (code splitting): the ticket list does not wait for them.
const NewTicketForm = lazy(() => import('./features/jobs/NewTicketForm').then((m) => ({ default: m.NewTicketForm })));
const LabsPage = lazy(() => import('./labs/LabsPage').then((m) => ({ default: m.LabsPage })));

/** The page frame: the navigation and the page that the address names. */
export function App() {
  const route = useRoute();
  return (
    <>
      <header className="top">
        <h1>Larkfield ticket desk</h1>
        <nav aria-label="Main">
          <a href="#/tickets" aria-current={route.page === 'tickets' ? 'page' : undefined}>
            Tickets
          </a>
          <a href="#/new" aria-current={route.page === 'new' ? 'page' : undefined}>
            New ticket
          </a>
          <a href="#/labs" aria-current={route.page === 'labs' ? 'page' : undefined}>
            Labs
          </a>
        </nav>
      </header>
      <main className="layout">
        <Suspense fallback={<p className="muted">Loading the page…</p>}>
          {route.page === 'new' && <NewTicketForm />}
          {route.page === 'labs' && <LabsPage lab={route.lab} />}
        </Suspense>
        {route.page === 'tickets' && (
          <>
            <TicketList selectedId={route.ticketId} />
            <div className="detail">
              {route.ticketId ? <TicketView ticketId={route.ticketId} /> : <p className="muted">Choose a ticket in the list.</p>}
            </div>
          </>
        )}
      </main>
    </>
  );
}
