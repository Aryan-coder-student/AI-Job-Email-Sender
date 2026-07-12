import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "@/shared/api/client";

import { QueuePage } from "./QueuePage";

vi.mock("@/features/runs/hooks", () => ({
  useActiveRun: () => ({ runId: "run-1" }),
}));

vi.mock("@/shared/api/client", () => ({
  api: {
    artifact: vi.fn(),
    processMail: vi.fn(),
  },
}));

describe("QueuePage", () => {
  beforeEach(() => {
    vi.mocked(api.artifact).mockResolvedValue([]);
    vi.mocked(api.processMail).mockResolvedValue([
      { draft_id: "draft-1", to: "hr@acme.test", status: "dry_run" },
    ]);
  });

  it("processes mail with selected limit and dry-run values", async () => {
    const user = userEvent.setup();
    renderWithQuery(<QueuePage />);

    const dryRun = await screen.findByLabelText(/dry run/i);
    await user.click(dryRun);
    await user.clear(screen.getByLabelText(/limit/i));
    await user.type(screen.getByLabelText(/limit/i), "3");
    await user.click(screen.getByRole("button", { name: /process/i }));

    await waitFor(() => {
      expect(api.processMail).toHaveBeenCalledWith("run-1", {
        dry_run: false,
        limit: 3,
      });
    });
    expect(await screen.findByText(/dry run is off/i)).toBeInTheDocument();
  });

  it("defaults to dry-run processing", async () => {
    const user = userEvent.setup();
    renderWithQuery(<QueuePage />);

    await user.click(await screen.findByRole("button", { name: /process/i }));

    await waitFor(() => {
      expect(api.processMail).toHaveBeenCalledWith("run-1", {
        dry_run: true,
        limit: 10,
      });
    });
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
