import { NewTicketForm } from './features/jobs/NewTicketForm';
import { TicketList } from './features/tickets/TicketList';
import { TicketView } from './features/tickets/TicketView';
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
        </nav>
      </header>
      <main className="layout">
        {route.page === 'new' ? (
          <NewTicketForm />
        ) : (
          <>
            <TicketList selectedId={route.page === 'tickets' ? route.ticketId : null} />
            <div className="detail">
              {route.page === 'tickets' && route.ticketId ? (
                <TicketView ticketId={route.ticketId} />
              ) : (
                <p className="muted">Choose a ticket in the list.</p>
              )}
            </div>
          </>
        )}
      </main>
    </>
  );
}
