// Module 1's JavaScript: show the newest tickets and send the form to the mock API.
// The page and the API come from the same address (http://127.0.0.1:8100), so the paths start with /.

/** Reads one page of tickets from the API. */
async function loadTickets(limit) {
  const response = await fetch(`/v1/tickets?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`The API answered ${response.status}`);
  }
  const page = await response.json();
  return page.items;
}

/** Makes one list item for a ticket. */
function ticketItem(ticket) {
  const item = document.createElement('li');
  const title = document.createElement('strong');
  title.textContent = `${ticket.ticket_id}: ${ticket.subject}`;
  const meta = document.createElement('div');
  meta.className = 'meta';
  meta.textContent = `${ticket.customer_name} · ${ticket.team} · ${ticket.status}`;
  item.append(title, meta);
  return item;
}

async function showTickets() {
  const list = document.querySelector('#tickets');
  try {
    const tickets = await loadTickets(10);
    list.replaceChildren(...tickets.map(ticketItem));
  } catch (error) {
    list.replaceChildren(`Could not load the tickets. ${error.message}`);
  }
}

const form = document.querySelector('#new-ticket');
const answer = document.querySelector('#answer');

form.addEventListener('submit', async (event) => {
  event.preventDefault(); // stay on this page: JavaScript sends the form
  const data = Object.fromEntries(new FormData(form));
  answer.textContent = 'Sending…';
  try {
    const response = await fetch('/v1/tickets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const body = await response.json();
    if (response.ok) {
      answer.textContent = `Saved as ${body.ticket_id}. AI work: ${body.state} (job ${body.job_id}).`;
      form.reset();
      showTickets();
    } else {
      answer.textContent = `Not saved: ${body.error.message} Fields: ${body.error.fields.join(', ')}`;
    }
  } catch (error) {
    answer.textContent = `The API did not answer. Is it running? (${error.message})`;
  }
});

showTickets();
