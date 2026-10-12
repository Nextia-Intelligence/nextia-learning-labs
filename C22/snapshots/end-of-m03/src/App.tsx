import { NewTicketForm } from './features/jobs/NewTicketForm';
import { TicketList } from './features/tickets/TicketList';
import { TicketView } from './features/tickets/TicketView';
import { LabsPage } from './labs/LabsPage';
import { useRoute } from './router';

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
        {route.page === 'new' && <NewTicketForm />}
        {route.page === 'labs' && <LabsPage lab={route.lab} />}
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
