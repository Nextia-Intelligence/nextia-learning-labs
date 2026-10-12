import { STATUSES, type Status } from '../../api/types';
import { useSetStatus } from './queries';

/** Changes the ticket's status. The change shows at once; if the server refuses it, it goes back. */
export function StatusSelect({ ticketId, status }: { ticketId: string; status: Status }) {
  const change = useSetStatus(ticketId);
  return (
    <div className="toolbar">
      <label>
        Status{' '}
        <select value={status} onChange={(e) => change.mutate(e.target.value as Status)}>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </label>
      {change.isError && (
        <span className="error" role="alert">
          The status was not changed: {change.error.message}
        </span>
      )}
    </div>
  );
}
