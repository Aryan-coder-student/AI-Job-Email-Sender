import { useMutation, useQuery } from "@tanstack/react-query";
import { PlayCircle } from "lucide-react";

import { useActiveRun } from "@/features/runs/hooks";
import { api } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { DataTable, Td, Th } from "@/shared/ui/data-table";
import type { MailQueueResult } from "@/shared/types/pipeline";

export function QueuePage() {
  const { runId } = useActiveRun();
  const { data: mail = [] } = useQuery({
    queryKey: ["artifact", runId, "mail"],
    queryFn: () => api.artifact<MailQueueResult[]>(runId, "mail"),
  });
  const processMail = useMutation({
    mutationFn: () => api.processMail(runId, { dry_run: true, limit: 10 }),
  });
  const rows = processMail.data ?? mail;

  return (
    <div className="grid gap-4">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-semibold">Mail queue</h1>
          <p className="text-sm text-muted-foreground">Inspect queued, sent, failed, and dry-run results.</p>
        </div>
        <Button onClick={() => processMail.mutate()}>
          <PlayCircle className="h-4 w-4" />
          Process dry run
        </Button>
      </div>
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
            </tbody>
          </DataTable>
        </CardContent>
      </Card>
    </div>
  );
}
