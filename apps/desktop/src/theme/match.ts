// Match category presentation metadata.
// Status is always conveyed with a label + icon, never color alone.

export type MatchCategoryKey = "strong" | "consider" | "stretch" | "low";

export const matchCategoryMeta: Record<
  string,
  { label: string; tone: "success" | "accent" | "warning" | "error"; description: string }
> = {
  strong_match: {
    label: "Strong Match",
    tone: "success",
    description: "Your verified profile aligns closely with most requirements.",
  },
  worth_considering: {
    label: "Worth Considering",
    tone: "accent",
    description: "Good overlap with some gaps to address truthfully.",
  },
  stretch_opportunity: {
    label: "Stretch Opportunity",
    tone: "warning",
    description: "Partial alignment; review the gaps before applying.",
  },
  low_match: {
    label: "Low Match",
    tone: "error",
    description: "Limited overlap with current verified experience.",
  },
};

export const applicationStatusMeta: Record<string, { label: string; tone: string }> = {
  saved: { label: "Saved", tone: "neutral" },
  planning: { label: "Planning", tone: "neutral" },
  documents_in_progress: { label: "Documents in Progress", tone: "warning" },
  ready_to_apply: { label: "Ready to Apply", tone: "accent" },
  applied: { label: "Applied", tone: "accent" },
  assessment: { label: "Assessment", tone: "warning" },
  interview: { label: "Interview", tone: "accent" },
  offer: { label: "Offer", tone: "success" },
  rejected: { label: "Rejected", tone: "error" },
  withdrawn: { label: "Withdrawn", tone: "neutral" },
  closed: { label: "Closed", tone: "neutral" },
};

export const verificationMeta: Record<string, { label: string; tone: string }> = {
  user_confirmed: { label: "User confirmed", tone: "success" },
  imported_pending: { label: "Imported - needs confirmation", tone: "warning" },
  extracted: { label: "Extracted from document", tone: "warning" },
  ai_suggested: { label: "AI suggested", tone: "accent" },
  unverified: { label: "Unverified", tone: "neutral" },
  outdated: { label: "Outdated", tone: "error" },
};

export function scoreToCategory(score: number): string {
  if (score >= 75) return "strong_match";
  if (score >= 55) return "worth_considering";
  if (score >= 35) return "stretch_opportunity";
  return "low_match";
}
