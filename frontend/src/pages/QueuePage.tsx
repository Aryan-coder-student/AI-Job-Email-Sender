import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { PlayCircle } from "lucide-react";
import { useState } from "react";

import { useActiveRun } from "@/features/runs/hooks";
import { NoSelectedRunState } from "@/features/runs/run-picker";
import { api } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { DataTable, Td, Th } from "@/shared/ui/data-table";
import { Field, Input } from "@/shared/ui/form";
import type { MailQueueResult } from "@/shared/types/pipeline";

export function QueuePage() {
  const activeRun = useActiveRun();
  const { runId } = activeRun;
  const queryClient = useQueryClient();
  const [dryRun, setDryRun] = useState(true);
  const [limit, setLimit] = useState("10");
  const processLimit = Math.min(Math.max(Number(limit) || 1, 1), 100);
  const { data: mail = [] } = useQuery({
    queryKey: ["artifact", runId, "mail"],
    queryFn: () => api.artifact<MailQueueResult[]>(runId as string, "mail"),
    enabled: Boolean(runId),
  });
  const processMail = useMutation({
    mutationFn: () => api.processMail(runId as string, { dry_run: dryRun, limit: processLimit }),
    onSuccess: (rows) => {
      queryClient.setQueryData(["artifact", runId, "mail"], rows);
    },
  });
  const rows = processMail.data ?? mail;

  if (!runId) {
    return <NoSelectedRunState missing={activeRun.isSelectedRunMissing} />;
  }

  return (
    <div className="grid gap-4">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-semibold">Mail queue</h1>
          <p className="text-sm text-muted-foreground">Inspect queued, sent, failed, and dry-run results.</p>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex h-9 items-center gap-2 rounded-md border px-3 text-sm font-medium">
            <input
              type="checkbox"
              checked={dryRun}
              onChange={(event) => setDryRun(event.target.checked)}
            />
            Dry run
          </label>
          <Field label="Limit">
            <Input
              className="w-24"
              min={1}
              max={100}
              type="number"
              value={limit}
              onChange={(event) => setLimit(event.target.value)}
            />
          </Field>
          <Button onClick={() => processMail.mutate()} disabled={processMail.isPending}>
            <PlayCircle className="h-4 w-4" />
            {processMail.isPending ? "Processing" : "Process"}
          </Button>
        </div>
      </div>
      {!dryRun ? (
        <p className="text-sm font-medium text-destructive">
          Dry run is off. Processing can send real email through the configured provider.
        </p>
      ) : null}
      <Card>
        <CardHeader>
          <CardTitle>Results</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable>
            <thead>
              <tr>
                <Th>Draft</Th>
                <Th>Recipient</Th>
                <Th>Status</Th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.draft_id}>
                  <Td className="font-mono">{row.draft_id}</Td>
                  <Td>{row.to}</Td>
                  <Td>{row.status}</Td>
                </tr>
              ))}
              {rows.length === 0 ? (
                <tr>
                  <Td colSpan={3} className="text-muted-foreground">No mail results yet.</Td>
                </tr>
              ) : null}
            </tbody>
          </DataTable>
          {processMail.isError ? (
            <p className="mt-3 text-sm text-destructive">Could not process the mail queue.</p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
