import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { DataTable, Td, Th } from "@/shared/ui/data-table";
import type {
  ArtifactType,
  EmailDraftMap,
  GraphArtifact,
  MailQueueResult,
  MatchResult,
} from "@/shared/types/pipeline";

export function ArtifactPanel({
  runId,
  artifactType,
}: {
  runId: string;
  artifactType: ArtifactType;
}) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["artifact", runId, artifactType],
    queryFn: () => api.artifact<unknown>(runId, artifactType),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>{artifactType} artifact</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading artifact...</p>
        ) : error ? (
          <p className="text-sm text-destructive">Artifact is not available.</p>
        ) : (
          <div className="grid gap-4">
            <ArtifactSummary artifactType={artifactType} data={data} />
            <details className="rounded-md border border-border">
              <summary className="cursor-pointer px-3 py-2 text-sm font-semibold">Raw JSON</summary>
              <pre className="max-h-96 overflow-auto border-t bg-muted p-3 text-xs">
                {JSON.stringify(data, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ArtifactSummary({
  artifactType,
  data,
}: {
  artifactType: ArtifactType;
  data: unknown;
}) {
  if (artifactType === "graph" && isGraphArtifact(data)) {
    return (
      <div className="grid gap-3 sm:grid-cols-3">
        <SummaryStat label="Candidate graph" value={formatGraphBuild(data.candidate)} />
        <SummaryStat label="Company graph" value={formatGraphBuild(data.companies)} />
        <SummaryStat
          label="Vector index"
          value={`${data.vector_index?.projects_indexed ?? 0} projects · ${data.vector_index?.jobs_indexed ?? 0} jobs`}
        />
      </div>
    );
  }

  if (artifactType === "matches" && isMatchesArtifact(data)) {
    const summaries = Object.entries(data).map(([companyName, matches]) => ({
      companyName,
      count: matches.length,
      topScore: matches[0]?.final_score ?? 0,
    }));

    return (
      <DataTable>
        <thead>
          <tr>
            <Th>Company</Th>
            <Th>Matches</Th>
            <Th>Top final score</Th>
          </tr>
        </thead>
        <tbody>
          {summaries.map((summary) => (
            <tr key={summary.companyName}>
              <Td>{summary.companyName}</Td>
              <Td>{summary.count}</Td>
              <Td>{Math.round(summary.topScore * 100)}%</Td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    );
  }

  if (artifactType === "drafts" && isDraftArtifact(data)) {
    return (
      <DataTable>
        <thead>
          <tr>
            <Th>Company</Th>
            <Th>Recipient</Th>
            <Th>Subject</Th>
            <Th>Status</Th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(data).map(([companyName, draft]) => (
            <tr key={companyName}>
              <Td>{companyName}</Td>
              <Td>{draft.to}</Td>
              <Td>{draft.subject}</Td>
              <Td>{draft.status}</Td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    );
  }

  if (artifactType === "mail" && Array.isArray(data)) {
    return (
      <DataTable>
        <thead>
          <tr>
            <Th>Draft</Th>
            <Th>Recipient</Th>
            <Th>Status</Th>
            <Th>Provider</Th>
            <Th>Message / Error</Th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => {
            const mailRow = row as MailQueueResult;
            return (
              <tr key={`${mailRow.draft_id}-${index}`}>
                <Td className="font-mono">{mailRow.draft_id}</Td>
                <Td>{mailRow.to ?? "-"}</Td>
                <Td>{mailRow.status}</Td>
                <Td>{mailRow.provider ?? "-"}</Td>
                <Td>{mailRow.message_id ?? mailRow.error ?? "-"}</Td>
              </tr>
            );
          })}
        </tbody>
      </DataTable>
    );
  }

  return <p className="text-sm text-muted-foreground">Summary view is not available for this artifact.</p>;
}

function SummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-muted/30 p-3">
      <div className="text-xs font-semibold uppercase tracking-normal text-muted-foreground">{label}</div>
      <div className="mt-1 text-sm font-semibold">{value}</div>
    </div>
  );
}

function formatGraphBuild(build: GraphArtifact["candidate"]) {
  if (!build) {
    return "Not available";
  }

  return `${build.nodes_upserted} nodes · ${build.edges_upserted} edges`;
}

function isGraphArtifact(data: unknown): data is GraphArtifact {
  return typeof data === "object" && data !== null && ("candidate" in data || "companies" in data || "vector_index" in data);
}

function isMatchesArtifact(data: unknown): data is Record<string, MatchResult[]> {
  return typeof data === "object" && data !== null && !Array.isArray(data);
}

function isDraftArtifact(data: unknown): data is EmailDraftMap {
  return typeof data === "object" && data !== null && !Array.isArray(data);
}
