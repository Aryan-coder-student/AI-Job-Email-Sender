import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "@/shared/api/client";
import type { MatchResult } from "@/shared/types/pipeline";

import { MatchesPage } from "./MatchesPage";

vi.mock("@/features/runs/hooks", () => ({
  useActiveRun: () => ({
    runId: "run-1",
    isSelectedRunMissing: false,
  }),
}));

vi.mock("@/shared/api/client", () => ({
  api: {
    artifact: vi.fn(),
  },
}));

describe("MatchesPage", () => {
  beforeEach(() => {
    vi.mocked(api.artifact).mockResolvedValue({
      "10up": [
        {
          project_id: "project-1",
          project_name: "AgroScan_Pro",
          graph_score: 0.34,
          embedding_score: 0.1,
          llm_score: 0.2,
          final_score: 0.22,
          explanation: "Strong overlap.",
          paths: [
            {
              company_name: "10up",
              project_name: "AgroScan_Pro",
              path_labels: ["Company", "LOOKS_FOR", "Capability", "DEMONSTRATES", "Project"],
              graph_score: 0.34,
              match_source: "company_capability",
            },
          ],
        },
        {
          project_id: "project-2",
          project_name: "Sentimental-analysis",
          graph_score: 0,
          embedding_score: 0.05,
          llm_score: 0.05,
          final_score: 0.03,
          explanation: "Weak graph evidence.",
          paths: [],
        },
      ] satisfies MatchResult[],
    });
  });

  it("renders graph path labels when they exist", async () => {
    const user = userEvent.setup();
    renderWithQuery(<MatchesPage />);

    await user.click(await screen.findByRole("button", { name: /10up/i }));

    expect(screen.getByText(/company capability/i)).toBeInTheDocument();
    expect(screen.getByText("LOOKS_FOR")).toBeInTheDocument();
    expect(screen.getByText("DEMONSTRATES")).toBeInTheDocument();
  });

  it("shows zero-score diagnostics for empty graph paths", async () => {
    const user = userEvent.setup();
    renderWithQuery(<MatchesPage />);

    await user.click(await screen.findByRole("button", { name: /10up/i }));

    expect(await screen.findByText(/no graph paths were found/i)).toBeInTheDocument();
    expect(screen.getByText(/technology-only overlap/i)).toBeInTheDocument();
  });
});

function renderWithQuery(ui: ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>,
  );
}
