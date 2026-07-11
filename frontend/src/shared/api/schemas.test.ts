import { describe, expect, it } from "vitest";

import { draftUpdateSchema, newRunSchema } from "@/shared/api/schemas";

describe("frontend schemas", () => {
  it("validates run options", () => {
    const parsed = newRunSchema.parse({
      target_company: "10up",
      companies_url: "https://docs.google.com/spreadsheets/d/sheet-id/edit#gid=1",
      recipient_email: "",
      job_url: "",
      max_repos: "25",
      max_companies: "10",
      top_matches: "5",
      dry_run: true,
      no_enqueue: false,
      skip_enrichment: false,
      clear_graph: false,
    });

    expect(parsed.max_repos).toBe(25);
    expect(parsed.companies_url).toContain("docs.google.com");
  });

  it("rejects an empty draft body", () => {
    const result = draftUpdateSchema.safeParse({
      to: "hr@example.com",
      subject: "Hello",
      body_text: "",
    });

    expect(result.success).toBe(false);
  });
});
