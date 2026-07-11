import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";

import { useActiveRun } from "@/features/runs/hooks";
import { api } from "@/shared/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { ProgressScore } from "@/shared/ui/progress-score";
import type { MatchResult } from "@/shared/types/pipeline";

export function MatchesPage() {
  const { runId } = useActiveRun();
  const { data: matchesData, isLoading } = useQuery({
    queryKey: ["artifact", runId, "matches"],
    queryFn: () => api.artifact<Record<string, MatchResult[]>>(runId, "matches"),
  });

  const entries = matchesData && typeof matchesData === "object" && !Array.isArray(matchesData)
    ? Object.entries(matchesData)
    : [];

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
                <p className="text-sm text-muted-foreground">{match.explanation}</p>
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
