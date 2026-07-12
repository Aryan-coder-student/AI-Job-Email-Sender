import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { PipelineRun } from "@/shared/types/pipeline";

vi.mock("@/shared/api/client", () => ({
  api: {
    listRuns: vi.fn(),
  },
  createRunEventSource: vi.fn(),
}));

import { api } from "@/shared/api/client";
import { NoSelectedRunState, RunPicker } from "@/features/runs/run-picker";

const runs: PipelineRun[] = [
  {
    run_id: "run-1",
    status: "completed",
    created_at: "2026-07-11T00:00:00.000Z",
    updated_at: "2026-07-11T00:00:00.000Z",
    config: { target_company: "Acme" },
    steps: [],
    latest_error: null,
    logs: [],
  },
  {
    run_id: "run-2",
    status: "running",
    created_at: "2026-07-11T00:00:00.000Z",
    updated_at: "2026-07-11T00:00:00.000Z",
    config: {},
    steps: [],
    latest_error: null,
    logs: [],
  },
];

function renderWithProviders(children: ReactNode, initialEntries = ["/candidate"]) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        {children}
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function LocationProbe() {
  const location = useLocation();
  return <output aria-label="location">{location.search}</output>;
}

describe("RunPicker", () => {
  beforeEach(() => {
    vi.mocked(api.listRuns).mockResolvedValue(runs);
  });

  it("lists runs and persists the selected run in the URL", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RunPicker />);

    await screen.findByRole("option", { name: /run-2/i });
    const picker = screen.getByRole("combobox", { name: /active run/i });
    expect(picker).toHaveValue("run-1");
    await user.selectOptions(picker, "run-2");

    expect(screen.getByLabelText("location")).toHaveTextContent("?run=run-2");
    expect(screen.getByRole("link", { name: /open selected run/i })).toHaveAttribute("href", "/runs/run-2");
  });

  it("renders an explicit no-selection state", () => {
    render(<NoSelectedRunState />);

    expect(screen.getByText(/select a run/i)).toBeInTheDocument();
  });
});
