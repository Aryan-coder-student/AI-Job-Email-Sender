import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "@/shared/api/client";

import { ArtifactPanel } from "./artifact-panel";

vi.mock("@/shared/api/client", () => ({
  api: {
    artifact: vi.fn(),
  },
}));

describe("ArtifactPanel", () => {
  beforeEach(() => {
    vi.mocked(api.artifact).mockReset();
  });

  it("renders a graph summary ahead of raw JSON", async () => {
    vi.mocked(api.artifact).mockResolvedValue({
      candidate: { nodes_upserted: 12, edges_upserted: 20 },
      companies: { nodes_upserted: 30, edges_upserted: 45 },
      vector_index: { projects_indexed: 8, jobs_indexed: 5 },
    });

    renderWithQuery(<ArtifactPanel runId="run-1" artifactType="graph" />);

    expect(await screen.findByText(/12 nodes/i)).toBeInTheDocument();
    expect(screen.getByText(/8 projects/i)).toBeInTheDocument();
    expect(screen.getByText(/raw json/i)).toBeInTheDocument();
  });

  it("renders typed draft and mail summaries", async () => {
    vi.mocked(api.artifact)
      .mockResolvedValueOnce({
        Acme: {
          draft_id: "draft-acme",
          to: "hr@acme.test",
          subject: "Hello",
          body_text: "Hi",
          body_html: null,
          company_name: "Acme",
          project_name: "Project",
          status: "draft",
          metadata: {},
        },
      })
      .mockResolvedValueOnce([
        {
          draft_id: "draft-acme",
          to: "hr@acme.test",
          status: "sent",
          provider: "gmail",
          message_id: "msg-1",
        },
      ]);

    const { rerender } = renderWithQuery(<ArtifactPanel runId="run-1" artifactType="drafts" />);
    expect(await screen.findByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Acme")).toBeInTheDocument();

    rerender(
      <QueryClientProvider client={buildQueryClient()}>
        <ArtifactPanel runId="run-1" artifactType="mail" />
      </QueryClientProvider>,
    );

    expect(await screen.findByText("gmail")).toBeInTheDocument();
    expect(screen.getByText("msg-1")).toBeInTheDocument();
  });
});

function renderWithQuery(ui: ReactNode) {
  return render(
    <QueryClientProvider client={buildQueryClient()}>
      {ui}
    </QueryClientProvider>,
  );
}

function buildQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
}
