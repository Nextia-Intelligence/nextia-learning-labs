import { describe, expect, it } from "vitest";
import { FR_KEYS, KEYS, frTypography, translate } from "./i18n";

describe("labels", () => {
  it("has a French label for every English label", () => {
    expect([...FR_KEYS].sort()).toEqual([...KEYS].sort());
  });
  it("puts a no-break space before : ; ! ? in French", () => {
    expect(frTypography("Erreur : non ; oui ! vrai ?")).toBe("Erreur : non ; oui ! vrai ?");
    expect(frTypography("Prix:")).toBe("Prix :");
    expect(frTypography("17:52 et http://x")).toBe("17:52 et http://x");
    for (const k of KEYS) {
      const s = translate("fr", k);
      expect(s, k).not.toMatch(/ [:;!?](\s|$)/);
    }
  });
  it("fills in the values", () => {
    expect(translate("en", "runs_count", { shown: 2, total: 3, flagged: 1 })).toBe("2 of 3 runs, 1 flagged");
  });
  it("labels the budget as an assumption", () => {
    expect(translate("en", "budget", { budget: "0.002" })).toContain("assumption: Omar's budget");
  });
  it("says what the data is", () => {
    expect(translate("en", "honesty_week")).toContain("real recorded model decisions from the agents course, constructed traffic and practice incidents");
  });
});
