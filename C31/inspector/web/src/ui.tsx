import type { ReactNode } from "react";
import { label, useApp } from "./context";
import type { FlagName } from "./types";

export function FlagBadge({ name }: { name: FlagName }) {
  const { t } = useApp();
  return (
    <span className={`badge flag flag-${name}`}>
      <span aria-hidden="true">⚑ </span>
      {label(t, "flag_", name)}
    </span>
  );
}

export function Flags({ names }: { names: FlagName[] }) {
  const { t } = useApp();
  if (!names.length) return <span className="muted">{t("none")}</span>;
  return (
    <span className="badges">
      {names.map((n) => (
        <FlagBadge key={n} name={n} />
      ))}
    </span>
  );
}

export function Outcome({ value }: { value: string }) {
  const { t } = useApp();
  return <span className={`badge outcome outcome-${value}`}>{label(t, "out_", value)}</span>;
}

export function Constructed() {
  const { t } = useApp();
  return <span className="badge constructed">{t("constructed")}</span>;
}

export function Loading() {
  const { t } = useApp();
  return (
    <p className="muted" role="status">
      {t("loading")}
    </p>
  );
}

export function ErrorBox({ message }: { message: string }) {
  const { t, lang } = useApp();
  return (
    <div className="callout danger" role="alert">
      <strong>{t("error")}{lang === "fr" ? "\u00a0: " : ": "}</strong>
      {message}
    </div>
  );
}

export function Stat({ name, children }: { name: string; children: ReactNode }) {
  return (
    <div className="stat">
      <dt>{name}</dt>
      <dd>{children}</dd>
    </div>
  );
}

export function Select({ id, labelText, value, onChange, options, all }: {
  id: string;
  labelText: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; text: string }[];
  all?: string;
}) {
  return (
    <div className="field">
      <label htmlFor={id}>{labelText}</label>
      <select id={id} value={value} onChange={(e) => onChange(e.target.value)}>
        {all !== undefined && <option value="">{all}</option>}
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.text}
          </option>
        ))}
      </select>
    </div>
  );
}
