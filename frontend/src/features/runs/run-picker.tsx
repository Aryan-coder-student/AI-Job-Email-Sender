import type { ChangeEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";

import { RUN_QUERY_PARAM, useRuns } from "@/features/runs/hooks";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { cn } from "@/shared/utils/cn";

export function RunPicker() {
  const { data: runs = [], isLoading } = useRuns();
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedRunId = searchParams.get(RUN_QUERY_PARAM) || "";
  const selectedRun = runs.find((run) => run.run_id === selectedRunId) ?? runs[0];

  const handleChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const nextParams = new URLSearchParams(searchParams);
    if (event.target.value) {
      nextParams.set(RUN_QUERY_PARAM, event.target.value);
    } else {
      nextParams.delete(RUN_QUERY_PARAM);
    }
    setSearchParams(nextParams, { replace: true });
  };

  return (
    <div className="flex min-w-0 items-center gap-2">
      <label className="sr-only" htmlFor="active-run-picker">Active run</label>
      <select
        id="active-run-picker"
        className={cn(
          "h-9 max-w-[46vw] rounded-md border border-input bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring sm:w-56",
          !selectedRunId && "text-muted-foreground",
        )}
        disabled={isLoading || runs.length === 0}
        value={selectedRun?.run_id ?? ""}
        onChange={handleChange}
      >
        <option value="">{runs.length === 0 ? "No runs" : "No run selected"}</option>
        {runs.map((run) => (
          <option key={run.run_id} value={run.run_id}>
            {optionLabel(run)}
          </option>
        ))}
      </select>
      {selectedRun ? (
        <Badge tone={selectedRun.status === "completed" ? "green" : "blue"}>
          {selectedRun.status}
        </Badge>
      ) : null}
      {selectedRunId ? (
        <Button asChild aria-label="Open selected run" size="icon" variant="outline">
          <Link to={`/runs/${selectedRunId}`}>
            <ArrowUpRight className="h-4 w-4" />
          </Link>
        </Button>
      ) : null}
    </div>
  );
}

function optionLabel(run: { run_id: string; status: string; config: Record<string, unknown> }) {
  const targetCompany = String(run.config.target_company ?? "").trim();
  return targetCompany
    ? `${run.run_id} · ${run.status} · ${targetCompany}`
    : `${run.run_id} · ${run.status}`;
}

export function NoSelectedRunState({ missing = false }: { missing?: boolean }) {
  return (
    <div className="rounded-md border border-dashed border-border p-4 text-sm text-muted-foreground">
      {missing ? "Selected run was not found." : "Select a run to view this workspace."}
    </div>
  );
}
