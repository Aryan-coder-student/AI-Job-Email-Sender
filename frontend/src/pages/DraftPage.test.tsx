import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "@/shared/api/client";
import type { EmailDraftMap } from "@/shared/types/pipeline";

import { DraftPage } from "./DraftPage";

vi.mock("@/features/runs/hooks", () => ({
  useActiveRun: () => ({ runId: "run-1" }),
}));

vi.mock("@/shared/api/client", () => ({
  api: {
    artifact: vi.fn(),
    updateDraft: vi.fn(),
    enqueueDraft: vi.fn(),
  },
}));

describe("DraftPage", () => {
  beforeEach(() => {
    vi.mocked(api.artifact).mockResolvedValue(drafts());
    vi.mocked(api.updateDraft).mockResolvedValue({
      Acme: { ...drafts().Acme, subject: "Updated subject" },
    });
    vi.mocked(api.enqueueDraft).mockResolvedValue({
      Acme: { ...drafts().Acme, status: "queued" },
    });
  });

  it("edits and saves a draft for a company", async () => {
    const user = userEvent.setup();
    renderWithQuery(<DraftPage />);

    await user.click(await screen.findByRole("button", { name: /acme/i }));
    await user.click(screen.getByRole("button", { name: /edit/i }));
    await user.clear(screen.getByLabelText(/subject/i));
    await user.type(screen.getByLabelText(/subject/i), "Updated subject");
    await user.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(api.updateDraft).toHaveBeenCalledWith("run-1", {
        company_name: "Acme",
        to: "hr@acme.test",
        subject: "Updated subject",
        body_text: "Hello",
        body_html: null,
      });
    });
  });

  it("keeps local content visible when save fails", async () => {
    vi.mocked(api.updateDraft).mockRejectedValueOnce(new Error("Nope"));
    const user = userEvent.setup();
    renderWithQuery(<DraftPage />);

    await user.click(await screen.findByRole("button", { name: /acme/i }));
    await user.click(screen.getByRole("button", { name: /edit/i }));
    await user.clear(screen.getByLabelText(/text body/i));
    await user.type(screen.getByLabelText(/text body/i), "Still here");
    await user.click(screen.getByRole("button", { name: /save/i }));

    expect(await screen.findByText(/could not save this draft/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue("Still here")).toBeInTheDocument();
  });
});

function renderWithQuery(ui: ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>,
  );
}

function drafts(): EmailDraftMap {
  return {
    Acme: {
      draft_id: "draft-acme",
      to: "hr@acme.test",
      subject: "Old subject",
      body_text: "Hello",
      body_html: null,
      company_name: "Acme",
      project_name: "Project",
      status: "draft",
      metadata: {},
    },
  };
}
