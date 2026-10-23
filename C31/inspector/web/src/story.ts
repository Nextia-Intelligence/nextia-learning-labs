// The audit story's words. English uses the sentence of the course's story.py (sent by the API);
// French builds the same sentence from the record's fields.

import { frTypography, type Lang } from "./i18n";
import { num, waiting } from "./format";
import type { Actor, AuditRecord, Effect } from "./types";

const ROLE: Record<Lang, Record<string, string>> = {
  en: { agent: "support agent", team_lead: "team lead", grace: "support lead" },
  fr: { agent: "agent de soutien", team_lead: "chef d'équipe", grace: "responsable du soutien" },
};

export function role(lang: Lang, r: string | undefined): string {
  return (r && ROLE[lang][r]) || (r ?? "").replace(/_/g, " ");
}

export function effectText(lang: Lang, e: Effect | undefined): string {
  if (!e) return "";
  const amount = e.amount !== undefined ? num(lang, e.amount, 2) : "";
  if (lang === "fr") {
    if (e.tool === "request_refund") return `remboursement de ${amount} (${e.reason_code}) sur ${e.order_id}`;
    if (e.tool === "reship_item") return `réexpédition de ${e.sku} × ${e.quantity} sur ${e.order_id}`;
    if (e.tool === "create_return_label") return `étiquette de retour pour ${e.sku} (${e.label_reason}) sur ${e.order_id}`;
    return `${e.tool} sur ${e.order_id}`;
  }
  if (e.tool === "request_refund") return `refund ${amount} (${e.reason_code}) on ${e.order_id}`;
  if (e.tool === "reship_item") return `reship ${e.sku} x ${e.quantity} on ${e.order_id}`;
  if (e.tool === "create_return_label") return `return label for ${e.sku} (${e.label_reason}) on ${e.order_id}`;
  return `${e.tool} on ${e.order_id}`;
}

const OUTCOME_FR: Record<string, string> = {
  resolved: "résolu", handed_to_person: "transmis à une personne", asked_customer: "question au client",
  waiting_approval: "en attente d'approbation", stopped: "arrêté", failed: "échec",
};

function whoFr(a: Actor): string {
  if (a.kind === "person") return `${a.name ?? a.id} (${a.id}, ${role("fr", a.role)})`;
  if (a.kind === "agent") return `L'agent IA ${a.id} (${a.model ?? ""}, ${a.role ?? ""})`;
  return `Le flux de travail (${a.id})`;
}

function limitFr(lim: number | null | undefined): string {
  return lim === -1 || lim === null || lim === undefined ? "aucune limite" : `limite ${num("fr", lim)}`;
}

/** The French sentence of one audit record (the same facts as story.py's English sentence). */
export function sentenceFr(r: AuditRecord): string {
  const a = r.action;
  const who = whoFr(r.actor);
  let s = "";
  switch (r.type) {
    case "data_access": {
      const orders = (a.orders ?? []).join(", ") || r.subject.order_id || "";
      s = `${who} a lu ${a.tool}${orders ? ` (${orders})` : ""} : ${a.status}.`;
      break;
    }
    case "proposal": {
      const acts = (a.actions ?? []).map((x: Effect) => effectText("fr", x)).join(" ; ") || "aucun changement";
      const need = r.authority.needs_role;
      const ev = r.evidence.join(", ") || "aucune";
      s = `${who} a proposé : ${a.outcome} (règle ${a.rule}) : ${acts}.` +
        (need ? ` L'approbation demande un rôle ${role("fr", need)} ou plus.` : "") + ` Preuves lues : ${ev}.`;
      break;
    }
    case "approval":
    case "refusal": {
      const prop = r.refers_to.proposal ?? "?";
      if (a.decision === "refused_by_rules") {
        s = `${who} a voulu approuver la proposition de l'enregistrement ${prop} ; les règles l'ont refusé (${limitFr(r.authority.limit)}, il faut un rôle ${role("fr", r.authority.needs_role)}).`;
      } else {
        const dec = a.decision === "approved" ? "approuvé" : a.decision === "rejected" ? "refusé" : a.decision;
        s = `${who} a ${dec} la proposition de l'enregistrement ${prop}${a.wait_s ? ` après ${waiting(a.wait_s)}` : ""} (${limitFr(r.authority.limit)}).`;
      }
      break;
    }
    case "write": {
      const auth = r.refers_to.approval ?? "aucune";
      const out = a.outcome === "done" ? "fait" : String(a.outcome).toUpperCase();
      s = `${who} a envoyé ${effectText("fr", a.effect)} : ${out} (tentative ${a.attempt}, clé ${a.idempotency_key}). Autorité : l'approbation de l'enregistrement ${auth}.`;
      break;
    }
    case "handoff":
      s = `${who} a transmis le billet à ${a.to} (${a.code}).`;
      break;
    case "run_closed":
      s = `Le billet a été fermé : ${OUTCOME_FR[a.outcome] ?? String(a.outcome).replace(/_/g, " ")} (écritures faites : ${a.writes_done}, réponse : ${a.reply_status}).`;
      break;
    default:
      s = `${r.type} : ${JSON.stringify(a)}`;
  }
  return frTypography(s);
}
