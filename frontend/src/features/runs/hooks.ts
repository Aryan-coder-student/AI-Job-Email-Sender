import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/api/client";

export function useRuns() {
  return useQuery({
    queryKey: ["runs"],
    queryFn: api.listRuns,
  });
}

export function useActiveRun() {
  const runsQuery = useRuns();
  const run = runsQuery.data?.[0];

  return {
    ...runsQuery,
    run,
    runId: run?.run_id ?? "local-demo",
  };
}
