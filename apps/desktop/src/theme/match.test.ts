import { describe, it, expect } from "vitest";
import {
  scoreToCategory,
  matchCategoryMeta,
  applicationStatusMeta,
  verificationMeta,
} from "./match";

describe("scoreToCategory", () => {
  it("maps scores to the documented categories", () => {
    expect(scoreToCategory(90)).toBe("strong_match");
    expect(scoreToCategory(75)).toBe("strong_match");
    expect(scoreToCategory(70)).toBe("worth_considering");
    expect(scoreToCategory(55)).toBe("worth_considering");
    expect(scoreToCategory(40)).toBe("stretch_opportunity");
    expect(scoreToCategory(35)).toBe("stretch_opportunity");
    expect(scoreToCategory(20)).toBe("low_match");
  });
});

describe("category metadata", () => {
  it("defines a label and tone for every category", () => {
    Object.keys(matchCategoryMeta).forEach((key) => {
      expect(matchCategoryMeta[key].label.length).toBeGreaterThan(0);
      expect(["success", "accent", "warning", "error"]).toContain(
        matchCategoryMeta[key].tone
      );
    });
  });

  it("never uses purple tones", () => {
    const tones = Object.values(matchCategoryMeta).map((m) => m.tone);
    expect(tones).not.toContain("purple");
  });
});

describe("status metadata", () => {
  it("labels every application status", () => {
    const required = [
      "saved",
      "planning",
      "documents_in_progress",
      "ready_to_apply",
      "applied",
      "assessment",
      "interview",
      "offer",
      "rejected",
      "withdrawn",
      "closed",
    ];
    required.forEach((s) => {
      expect(applicationStatusMeta[s]).toBeDefined();
      expect(applicationStatusMeta[s].label.length).toBeGreaterThan(0);
    });
  });
});

describe("verification metadata", () => {
  it("labels every verification status", () => {
    const required = [
      "user_confirmed",
      "imported_pending",
      "extracted",
      "ai_suggested",
      "unverified",
      "outdated",
    ];
    required.forEach((s) => {
      expect(verificationMeta[s]).toBeDefined();
    });
  });
});
