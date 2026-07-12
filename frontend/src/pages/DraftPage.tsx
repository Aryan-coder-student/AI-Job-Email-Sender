import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, Send } from "lucide-react";
import { useState } from "react";

import { useActiveRun } from "@/features/runs/hooks";
import { NoSelectedRunState } from "@/features/runs/run-picker";
import { api } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import type { EmailDraft } from "@/shared/types/pipeline";

export function DraftPage() {
  const activeRun = useActiveRun();
  const { runId } = activeRun;
  const queryClient = useQueryClient();
  const { data: drafts } = useQuery({
    queryKey: ["artifact", runId, "drafts"],
    queryFn: () => api.artifact<Record<string, EmailDraft>>(runId as string, "drafts"),
    enabled: Boolean(runId),
  });
  const enqueueDraft = useMutation({
    mutationFn: () => api.enqueueDraft(runId as string),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["artifact", runId, "drafts"] }),
  });

  if (!runId) {
    return <NoSelectedRunState missing={activeRun.isSelectedRunMissing} />;
  }

  if (!drafts || typeof drafts !== "object") {
    return <p className="text-sm text-muted-foreground">Loading drafts...</p>;
  }

  const entries = Object.entries(drafts);

  return (
    <div className="grid gap-4">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-semibold">Email Drafts</h1>
          <p className="text-sm text-muted-foreground">
            {entries.length} draft(s) generated
          </p>
        </div>
        <Button type="button" disabled={enqueueDraft.isPending} onClick={() => enqueueDraft.mutate()}>
          <Send className="h-4 w-4" />
          Enqueue All
        </Button>
      </div>
      {entries.length === 0 ? (
        <p className="text-sm text-muted-foreground">No drafts have been generated yet.</p>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Drafts by Company</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            {entries.map(([companyName, draft]) => (
              <DraftSection key={companyName} companyName={companyName} draft={draft as EmailDraft} />
            ))}
          </CardContent>
        </Card>
      )}
      {enqueueDraft.isSuccess ? <p className="text-sm text-muted-foreground">All drafts queued.</p> : null}
    </div>
  );
}

function DraftSection({ companyName, draft }: { companyName: string; draft: EmailDraft }) {
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
        <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium">{draft.status ?? "draft"}</span>
      </button>
      {open ? (
        <div className="border-t p-3 grid gap-2 text-sm">
          <div><span className="font-semibold">To:</span> {draft.to ?? "—"}</div>
          <div><span className="font-semibold">Subject:</span> {draft.subject ?? "—"}</div>
          <pre className="max-h-60 overflow-auto rounded-md bg-muted p-3 text-xs whitespace-pre-wrap">
            {draft.body_text ?? ""}
          </pre>
        </div>
      ) : null}
    </div>
  );
}
