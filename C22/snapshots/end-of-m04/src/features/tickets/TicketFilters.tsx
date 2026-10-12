import { STATUSES, TEAMS, type TicketFilter } from '../../api/types';

/** The filters above the list. The parent owns the values; this component only shows and changes them. */
export function TicketFilters({ value, onChange }: { value: TicketFilter; onChange: (next: TicketFilter) => void }) {
  return (
    <form className="filters" role="search" onSubmit={(e) => e.preventDefault()}>
      <label>
        Search
        <input
          type="search"
          value={value.q}
          onChange={(e) => onChange({ ...value, q: e.target.value })}
          placeholder="Subject, ticket or customer"
        />
      </label>
      <label>
        Status
        <select value={value.status} onChange={(e) => onChange({ ...value, status: e.target.value as TicketFilter['status'] })}>
          <option value="">All</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </label>
      <label>
        Team
        <select value={value.team} onChange={(e) => onChange({ ...value, team: e.target.value as TicketFilter['team'] })}>
          <option value="">All</option>
          {TEAMS.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </label>
    </form>
  );
}
