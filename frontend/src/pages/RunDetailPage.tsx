import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, RefreshCw, RotateCcw } from "lucide-react";
import { useState } from "react";
import { useParams } from "react-router-dom";

import { ArtifactPanel } from "@/features/runs/artifact-panel";
import { useRunEvents } from "@/features/runs/hooks";
import { PipelineStepper } from "@/features/runs/pipeline-stepper";
import { NoSelectedRunState } from "@/features/runs/run-picker";
import { api } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import type { ArtifactType } from "@/shared/types/pipeline";

export function RunDetailPage() {
  const params = useParams();
  const runId = params.runId;
  const [artifactType, setArtifactType] = useState<ArtifactType>("resume");
  const queryClient = useQueryClient();
  useRunEvents(runId);
  const { data: run, isLoading } = useQuery({
    queryKey: ["run", runId],
    queryFn: () => api.getRun(runId as string),
    enabled: Boolean(runId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "created" || status === "running" ? 1500 : false;
    },
  });
  const retry = useMutation({
    mutationFn: () => api.retryRun(runId as string),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["run", runId] }),
  });
  const resume = useMutation({
    mutationFn: () => api.resumeRun(runId as string),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["run", runId] }),
  });

  const { data: matchesData } = useQuery({
    queryKey: ["artifact", runId, "matches"],
    queryFn: () => api.artifact<Record<string, unknown[]>>(runId as string, "matches"),
    enabled: run?.status === "completed" || run?.steps?.some((s) => s.key === "rank_projects" && s.status === "completed"),
  });

  const { data: draftsData } = useQuery({
    queryKey: ["artifact", runId, "drafts"],
    queryFn: () => api.artifact<Record<string, Record<string, unknown>>>(runId as string, "drafts"),
    enabled: run?.status === "completed" || run?.steps?.some((s) => s.key === "generate_draft" && s.status === "completed"),
  });

  if (!runId) {
    return <NoSelectedRunState />;
  }

  if (isLoading || !run) {
    return <p className="text-sm text-muted-foreground">Loading run...</p>;
  }

  const companyCount = (run.config.selected_companies as unknown[])?.length ?? 0;

  return (
    <div className="grid gap-4">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-semibold">Run {run.run_id}</h1>
          <p className="text-sm text-muted-foreground">
            {companyCount} companies selected · Status: {run.status}
          </p>
          {run.latest_error ? (
            <p className="mt-1 text-sm text-destructive">{run.latest_error}</p>
          ) : null}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => resume.mutate()}>
            <RotateCcw className="h-4 w-4" />
            Resume
          </Button>
          <Button variant="outline" onClick={() => retry.mutate()}>
            <RefreshCw className="h-4 w-4" />
            Retry
          </Button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <PipelineStepper
          steps={run.steps}
          onOpenArtifact={(type) => setArtifactType(type as ArtifactType)}
        />
        <div className="grid gap-4">
          <ArtifactPanel runId={runId} artifactType={artifactType} />
          <Card>
            <CardHeader>
              <CardTitle>Logs</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="max-h-48 overflow-auto rounded-md bg-muted p-3 text-xs">
                {run.logs.join("\n")}
              </pre>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Per-company Matches */}
      {matchesData && typeof matchesData === "object" && !Array.isArray(matchesData) ? (
        <Card>
          <CardHeader>
            <CardTitle>Matches by Company ({Object.keys(matchesData).length})</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            {Object.entries(matchesData).map(([companyName, companyMatches]) => (
              <CompanySection key={companyName} title={companyName} badge={`${Array.isArray(companyMatches) ? companyMatches.length : 0} matches`}>
                <pre className="max-h-60 overflow-auto rounded-md bg-muted p-3 text-xs">
                  {JSON.stringify(companyMatches, null, 2)}
                </pre>
              </CompanySection>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {/* Per-company Drafts */}
      {draftsData && typeof draftsData === "object" && !Array.isArray(draftsData) ? (
        <Card>
          <CardHeader>
            <CardTitle>Email Drafts ({Object.keys(draftsData).length})</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            {Object.entries(draftsData).map(([companyName, draft]) => (
              <CompanySection key={companyName} title={companyName} badge={(draft as Record<string, unknown>)?.status as string ?? "draft"}>
                <div className="grid gap-2 text-sm">
                  <div><span className="font-semibold">To:</span> {String((draft as Record<string, unknown>)?.to ?? "—")}</div>
                  <div><span className="font-semibold">Subject:</span> {String((draft as Record<string, unknown>)?.subject ?? "—")}</div>
                  <pre className="max-h-60 overflow-auto rounded-md bg-muted p-3 text-xs whitespace-pre-wrap">
                    {String((draft as Record<string, unknown>)?.body_text ?? "")}
                  </pre>
                </div>
              </CompanySection>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function CompanySection({ title, badge, children }: { title: string; badge?: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-md border">
      <button
        type="button"
        className="flex w-full items-center justify-between p-3 text-left text-sm font-semibold hover:bg-muted/50"
        onClick={() => setOpen((prev) => !prev)}
      >
        <span className="flex items-center gap-2">
          {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          {title}
        </span>
        {badge ? <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium">{badge}</span> : null}
      </button>
      {open ? <div className="border-t p-3">{children}</div> : null}
    </div>
  );
}
