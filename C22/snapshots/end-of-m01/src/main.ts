// The first page again, in TypeScript: the same list and form as bridge/app.js.
import { loadTickets, sendTicket, ticketLine } from './api';
import type { NewTicket } from './types';
import './styles.css';

const list = document.querySelector<HTMLUListElement>('#tickets')!;
const form = document.querySelector<HTMLFormElement>('#new-ticket')!;
const answer = document.querySelector<HTMLParagraphElement>('#answer')!;

async function showTickets() {
  try {
    const tickets = await loadTickets(10);
    list.replaceChildren(
      ...tickets.map((ticket) => {
        const item = document.createElement('li');
        item.className = 'row';
        item.textContent = ticketLine(ticket);
        return item;
      }),
    );
  } catch (error) {
    list.replaceChildren(`Could not load the tickets. ${(error as Error).message}`);
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault(); // stay on this page: the code sends the form
  const data = Object.fromEntries(new FormData(form)) as unknown as NewTicket;
  answer.textContent = 'Sending…';
  try {
    const result = await sendTicket(data);
    if (typeof result === 'string') {
      answer.textContent = result;
    } else {
      answer.textContent = `Saved as ${result.ticket_id}. AI work: ${result.state} (job ${result.job_id}).`;
      form.reset();
      void showTickets();
    }
  } catch (error) {
    answer.textContent = `The API did not answer. Is it running? (${(error as Error).message})`;
  }
});

void showTickets();
