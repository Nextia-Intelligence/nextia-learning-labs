import { describe, expect, it } from "vitest";
import { dayKey, dayRange, money, waiting, when } from "./format";
import { href, parseHash } from "./router";
import { effectText, sentenceFr } from "./story";
import type { AuditRecord } from "./types";

describe("format", () => {
  it("writes money in both languages", () => {
    expect(money("en", 0.011822)).toBe("US$0.01182");
    expect(money("fr", 0.011822)).toBe("0,01182 $ US");
  });
  it("writes a waiting time", () => {
    expect(waiting(55505.4)).toBe("15 h 25 min");
    expect(waiting(245)).toBe("4 min 05 s");
  });
  it("shows Toronto time with the fixed offset", () => {
    const ms = Date.parse("2026-10-14T21:52:00Z");
    expect(when("en", ms, -4, "dayhour")).toContain("17:52");
    expect(dayKey(ms, -4)).toBe("2026-10-14");
    const [a, b] = dayRange("2026-10-14", -4);
    expect(new Date(a).toISOString()).toBe("2026-10-14T04:00:00.000Z");
    expect(b - a).toBe(86_400_000);
  });
});

describe("router", () => {
  it("reads and writes hash routes", () => {
    expect(parseHash("#/run/R-1014-040?ds=week")).toEqual({ screen: "run", id: "R-1014-040", params: { ds: "week" } });
    expect(parseHash("")).toEqual({ screen: "runs", id: "", params: {} });
    expect(href("compare", "", { a: "R-1", b: "R-2", ds: "" })).toBe("#/compare?a=R-1&b=R-2");
  });
});

describe("audit story in French", () => {
  it("tells a write with its effect", () => {
    expect(effectText("fr", { tool: "request_refund", amount: 9.95, reason_code: "RFD-LATE", order_id: "LK-793996" }))
      .toBe("remboursement de 9,95 (RFD-LATE) sur LK-793996");
    const r = {
      seq: 672, at: "2026-10-15T13:17:22+00:00", type: "write", actor: { kind: "system", id: "support-workflow" },
      action: { effect: { tool: "request_refund", amount: 9.95, reason_code: "RFD-LATE", order_id: "LK-793996" }, outcome: "timeout", attempt: 1, idempotency_key: "797fbb5bbb9f8a7e" },
      authority: {}, evidence: [], subject: {}, trace_id: "", span_id: "", hash: "", prev: "", links_ok: true, sentence: "",
      refers_to: { proposal: null, approval: 671 },
    } as unknown as AuditRecord;
    expect(sentenceFr(r)).toBe("Le flux de travail (support-workflow) a envoyé remboursement de 9,95 (RFD-LATE) sur LK-793996 : TIMEOUT (tentative 1, clé 797fbb5bbb9f8a7e). Autorité : l'approbation de l'enregistrement 671.");
  });
});
