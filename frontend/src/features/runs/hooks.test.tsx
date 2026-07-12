import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { PipelineRun } from "@/shared/types/pipeline";

vi.mock("@/shared/api/client", () => ({
  api: {
    listRuns: vi.fn(),
  },
  createRunEventSource: vi.fn(),
}));

import { createRunEventSource, api } from "@/shared/api/client";
import { useActiveRun, useRunEvents } from "@/features/runs/hooks";

class FakeEventSource {
  close = vi.fn();
  private listeners = new Map<string, Set<EventListener>>();

  addEventListener(type: string, listener: EventListener) {
    this.listeners.set(type, this.listeners.get(type) ?? new Set());
    this.listeners.get(type)?.add(listener);
  }

  removeEventListener(type: string, listener: EventListener) {
    this.listeners.get(type)?.delete(listener);
  }

  dispatch(type: string, data: string) {
    this.listeners.get(type)?.forEach((listener) => {
      listener({ data } as MessageEvent<string>);
    });
  }
}

const run: PipelineRun = {
  run_id: "run-1",
  status: "running",
  created_at: "2026-07-11T00:00:00.000Z",
  updated_at: "2026-07-11T00:00:00.000Z",
  config: {},
  steps: [],
  latest_error: null,
  logs: [],
};

function renderWithProviders<TProps, TResult>(
  callback: (props: TProps) => TResult,
  options: { initialEntries?: string[]; initialProps: TProps },
) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={options.initialEntries ?? ["/"]}>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  );

  return {
    queryClient,
    ...renderHook(callback, { initialProps: options.initialProps, wrapper }),
  };
}

describe("run hooks", () => {
  beforeEach(() => {
    vi.mocked(api.listRuns).mockResolvedValue([run]);
    vi.mocked(createRunEventSource).mockReset();
  });

  it("updates the run cache from snapshot events and ignores heartbeats", async () => {
    const source = new FakeEventSource();
    vi.mocked(createRunEventSource).mockReturnValue(source as unknown as EventSource);

    const { queryClient, result, unmount } = renderWithProviders(() => useActiveRun(), {
      initialEntries: ["/candidate"],
      initialProps: undefined,
    });

    await waitFor(() => expect(result.current.runId).toBe("run-1"));

    const completedRun = { ...run, status: "completed" as const };
    source.dispatch("snapshot", JSON.stringify(completedRun));
    expect(queryClient.getQueryData(["run", "run-1"])).toMatchObject({ status: "completed" });

    source.dispatch("heartbeat", "{}");
    expect(queryClient.getQueryData(["run", "run-1"])).toMatchObject({ status: "completed" });

    unmount();
    expect(source.close).toHaveBeenCalled();
  });

  it("marks a selected run as missing when the URL points to an unknown run", async () => {
    const { result } = renderWithProviders(() => useActiveRun(), {
      initialEntries: ["/candidate?run=missing-run"],
      initialProps: undefined,
    });

    await waitFor(() => expect(result.current.isSelectedRunMissing).toBe(true));
    expect(result.current.runId).toBeUndefined();
  });

  it("closes the previous EventSource when the run changes", () => {
    const firstSource = new FakeEventSource();
    const secondSource = new FakeEventSource();
    vi.mocked(createRunEventSource)
      .mockReturnValueOnce(firstSource as unknown as EventSource)
      .mockReturnValueOnce(secondSource as unknown as EventSource);

    const { rerender, unmount } = renderWithProviders(
      ({ runId }: { runId: string }) => useRunEvents(runId),
      { initialProps: { runId: "run-1" } },
    );

    rerender({ runId: "run-2" });
    expect(firstSource.close).toHaveBeenCalled();

    unmount();
    expect(secondSource.close).toHaveBeenCalled();
  });
});
