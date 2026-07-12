import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";

import { useActiveRun } from "@/features/runs/hooks";
import { NoSelectedRunState } from "@/features/runs/run-picker";
import { api } from "@/shared/api/client";
import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { ProgressScore } from "@/shared/ui/progress-score";
import type { MatchPath, MatchResult } from "@/shared/types/pipeline";

export function MatchesPage() {
  const activeRun = useActiveRun();
  const { runId } = activeRun;
  const { data: matchesData, isLoading } = useQuery({
    queryKey: ["artifact", runId, "matches"],
    queryFn: () => api.artifact<Record<string, MatchResult[]>>(runId as string, "matches"),
    enabled: Boolean(runId),
  });

  const entries = matchesData && typeof matchesData === "object" && !Array.isArray(matchesData)
    ? Object.entries(matchesData)
    : [];

  if (!runId) {
    return <NoSelectedRunState missing={activeRun.isSelectedRunMissing} />;
  }

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Matches</h1>
        <p className="text-sm text-muted-foreground">
          Ranked project-company fit with score breakdown · {entries.length} companies
        </p>
      </div>
      {isLoading ? <p className="text-sm text-muted-foreground">Loading matches...</p> : null}
      {entries.length === 0 && !isLoading ? (
        <p className="text-sm text-muted-foreground">No matches available yet.</p>
      ) : null}
      <div className="grid gap-3">
        {entries.map(([companyName, companyMatches]) => (
          <CompanyMatchSection
            key={companyName}
            companyName={companyName}
            matches={Array.isArray(companyMatches) ? companyMatches : []}
          />
        ))}
      </div>
    </div>
  );
}

function CompanyMatchSection({ companyName, matches }: { companyName: string; matches: MatchResult[] }) {
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
          {companyName}
        </span>
        <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium">
          {matches.length} matches
        </span>
      </button>
      {open ? (
        <div className="border-t grid gap-3 p-3">
          {matches.map((match) => (
            <Card key={match.project_id}>
              <CardHeader>
                <CardTitle>{match.project_name}</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 lg:grid-cols-[1fr_280px]">
                <div className="grid gap-3">
                  <p className="text-sm text-muted-foreground">{match.explanation}</p>
                  {match.paths.length > 0 ? (
                    <div className="grid gap-2">
                      {match.paths.map((path, index) => (
                        <PathRow key={`${match.project_id}-${index}`} path={path} />
                      ))}
                    </div>
                  ) : null}
                  {showZeroGraphDiagnostics(match) ? (
                    <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                      No graph paths were found for this project yet. Common reasons are missing enrichment,
                      no capability or domain overlap, technology-only overlap that is not scored yet, or
                      candidate/company/job IDs that did not line up during ranking.
                    </div>
                  ) : null}
                </div>
                <div className="grid gap-2">
                  <ProgressScore label="Final" value={match.final_score} />
                  <ProgressScore label="Graph" value={match.graph_score} />
                  <ProgressScore label="Embedding" value={match.embedding_score} />
                  <ProgressScore label="LLM" value={match.llm_score} />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function PathRow({ path }: { path: MatchPath }) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/30 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="blue">{formatMatchSource(path.match_source)}</Badge>
        <span className="text-xs text-muted-foreground">
          {path.project_name} {"->"} {path.company_name}
        </span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {path.path_labels.map((label, index) => (
          <Badge key={`${label}-${index}`} tone="neutral">
            {label}
          </Badge>
        ))}
      </div>
    </div>
  );
}

function showZeroGraphDiagnostics(match: MatchResult) {
  return match.graph_score === 0 && match.paths.length === 0;
}

function formatMatchSource(matchSource: string) {
  return matchSource.split("_").join(" ");
}
