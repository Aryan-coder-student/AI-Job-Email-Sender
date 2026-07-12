import { useEffect, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { api, createRunEventSource } from "@/shared/api/client";
import type { PipelineRun } from "@/shared/types/pipeline";

export const RUN_QUERY_PARAM = "run";

export function useRuns() {
  return useQuery({
    queryKey: ["runs"],
    queryFn: api.listRuns,
  });
}

export function useActiveRun() {
  const runsQuery = useRuns();
  const [searchParams] = useSearchParams();
  const selectedRunId = searchParams.get(RUN_QUERY_PARAM) || undefined;
  const run = useMemo(() => {
    if (!runsQuery.data?.length) {
      return undefined;
    }

    if (!selectedRunId) {
      return runsQuery.data[0];
    }

    return runsQuery.data.find((item) => item.run_id === selectedRunId);
  }, [runsQuery.data, selectedRunId]);

  useRunEvents(run?.run_id);

  return {
    ...runsQuery,
    run,
    runId: run?.run_id,
    selectedRunId,
    hasSelectedRun: Boolean(selectedRunId || run),
    isSelectedRunMissing: Boolean(selectedRunId && runsQuery.data && !run),
  };
}

export function useRunEvents(runId: string | undefined) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!runId) {
      return undefined;
    }

    const eventSource = createRunEventSource(runId);
    if (!eventSource) {
      return undefined;
    }

    const handleSnapshot = (event: MessageEvent<string>) => {
      const run = parseRunSnapshot(event.data);
      if (!run) {
        return;
      }

      queryClient.setQueryData(["run", run.run_id], run);
      queryClient.setQueryData<PipelineRun[]>(["runs"], (currentRuns) => (
        upsertRun(currentRuns, run)
      ));
    };

    const handleError = () => {
      queryClient.invalidateQueries({ queryKey: ["run", runId] });
      eventSource.close();
    };

    eventSource.addEventListener("snapshot", handleSnapshot);
    eventSource.addEventListener("heartbeat", noop);
    eventSource.addEventListener("error", handleError);

    return () => {
      eventSource.removeEventListener("snapshot", handleSnapshot);
      eventSource.removeEventListener("heartbeat", noop);
      eventSource.removeEventListener("error", handleError);
      eventSource.close();
    };
  }, [queryClient, runId]);
}

function parseRunSnapshot(data: string): PipelineRun | null {
  try {
    const value = JSON.parse(data) as Partial<PipelineRun>;
    return typeof value.run_id === "string" ? (value as PipelineRun) : null;
  } catch {
    return null;
  }
}

function upsertRun(currentRuns: PipelineRun[] | undefined, run: PipelineRun) {
  if (!currentRuns) {
    return [run];
  }

  const hasRun = currentRuns.some((item) => item.run_id === run.run_id);
  if (!hasRun) {
    return [run, ...currentRuns];
  }

  return currentRuns.map((item) => (item.run_id === run.run_id ? run : item));
}

function noop() {}
