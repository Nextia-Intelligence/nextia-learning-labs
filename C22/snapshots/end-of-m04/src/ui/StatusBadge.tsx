import type { Status } from '../api/types';

const LABELS: Record<Status, string> = { open: 'Open', pending: 'Pending', resolved: 'Resolved', closed: 'Closed' };

/** A ticket's status as a small coloured label. The word is always visible, not only the colour. */
export function StatusBadge({ status }: { status: Status }) {
  return <span className={`badge badge-${status}`}>{LABELS[status]}</span>;
}
