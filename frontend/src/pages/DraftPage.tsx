import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ChevronDown, ChevronRight, Pencil, Send, X } from "lucide-react";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { useActiveRun } from "@/features/runs/hooks";
import { NoSelectedRunState } from "@/features/runs/run-picker";
import { api } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Field, Input, Textarea } from "@/shared/ui/form";
import type { DraftUpdatePayload, EmailDraft, EmailDraftMap } from "@/shared/types/pipeline";

export function DraftPage() {
  const activeRun = useActiveRun();
  const { runId } = activeRun;
  const queryClient = useQueryClient();
  const { data: drafts } = useQuery({
    queryKey: ["artifact", runId, "drafts"],
    queryFn: () => api.artifact<EmailDraftMap>(runId as string, "drafts"),
    enabled: Boolean(runId),
  });
  const updateDraft = useMutation({
    mutationFn: (payload: DraftUpdatePayload) => api.updateDraft(runId as string, payload),
    onSuccess: (updatedDrafts) => {
      queryClient.setQueryData(["artifact", runId, "drafts"], updatedDrafts);
    },
  });
  const enqueueDraft = useMutation({
    mutationFn: () => api.enqueueDraft(runId as string),
    onSuccess: (updatedDrafts) => {
      queryClient.setQueryData(["artifact", runId, "drafts"], updatedDrafts);
    },
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
        <Button
          type="button"
          onClick={() => enqueueDraft.mutate()}
          disabled={enqueueDraft.isPending || updateDraft.isPending || entries.length === 0}
        >
          <Send className="h-4 w-4" />
          {enqueueDraft.isPending ? "Enqueuing" : "Enqueue All"}
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
              <DraftSection
                key={companyName}
                companyName={companyName}
                draft={draft as EmailDraft}
                onSave={(payload) => updateDraft.mutateAsync(payload)}
              />
            ))}
          </CardContent>
        </Card>
      )}
      {enqueueDraft.isSuccess ? <p className="text-sm text-muted-foreground">All drafts queued.</p> : null}
      {enqueueDraft.isError ? <p className="text-sm text-destructive">Could not enqueue drafts.</p> : null}
    </div>
  );
}

function DraftSection({
  companyName,
  draft,
  onSave,
}: {
  companyName: string;
  draft: EmailDraft;
  onSave: (payload: DraftUpdatePayload) => Promise<EmailDraftMap>;
}) {
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(() => draftFormState(draft));
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!editing) setForm(draftFormState(draft));
  }, [draft, editing]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSaved(false);

    try {
      await onSave({ company_name: companyName, ...form });
      setEditing(false);
      setSaved(true);
    } catch {
      setError("Could not save this draft.");
    } finally {
      setSaving(false);
    }
  }

  function cancelEdit() {
    setForm(draftFormState(draft));
    setEditing(false);
    setError(null);
  }

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
        editing ? (
          <form className="grid gap-3 border-t p-3 text-sm" onSubmit={handleSubmit}>
            <Field label="To">
              <Input
                type="email"
                value={form.to}
                onChange={(event) => setForm((prev) => ({ ...prev, to: event.target.value }))}
              />
            </Field>
            <Field label="Subject">
              <Input
                value={form.subject}
                onChange={(event) => setForm((prev) => ({ ...prev, subject: event.target.value }))}
              />
            </Field>
            <Field label="Text body">
              <Textarea
                rows={8}
                value={form.body_text}
                onChange={(event) => setForm((prev) => ({ ...prev, body_text: event.target.value }))}
              />
            </Field>
            <Field label="HTML body">
              <Textarea
                rows={5}
                value={form.body_html ?? ""}
                onChange={(event) => setForm((prev) => ({ ...prev, body_html: event.target.value || null }))}
              />
            </Field>
            <div className="flex flex-wrap items-center gap-2">
              <Button type="submit" size="sm" disabled={saving}>
                <Check className="h-4 w-4" />
                {saving ? "Saving" : "Save"}
              </Button>
              <Button type="button" size="sm" variant="outline" onClick={cancelEdit} disabled={saving}>
                <X className="h-4 w-4" />
                Cancel
              </Button>
              {error ? <span className="text-xs text-destructive">{error}</span> : null}
            </div>
          </form>
        ) : (
          <div className="grid gap-3 border-t p-3 text-sm">
            <div><span className="font-semibold">To:</span> {draft.to ?? "-"}</div>
            <div><span className="font-semibold">Subject:</span> {draft.subject ?? "-"}</div>
            <pre className="max-h-60 overflow-auto rounded-md bg-muted p-3 text-xs whitespace-pre-wrap">
              {draft.body_text ?? ""}
            </pre>
            {draft.body_html ? (
              <pre className="max-h-40 overflow-auto rounded-md bg-muted/60 p-3 text-xs whitespace-pre-wrap">
                {draft.body_html}
              </pre>
            ) : null}
            <div className="flex flex-wrap items-center gap-2">
              <Button type="button" size="sm" variant="outline" onClick={() => setEditing(true)}>
                <Pencil className="h-4 w-4" />
                Edit
              </Button>
              {saved ? <span className="text-xs text-muted-foreground">Saved.</span> : null}
            </div>
          </div>
        )
      ) : null}
    </div>
  );
}

function draftFormState(draft: EmailDraft): Pick<
  EmailDraft,
  "to" | "subject" | "body_text" | "body_html"
> {
  return {
    to: draft.to ?? "",
    subject: draft.subject ?? "",
    body_text: draft.body_text ?? "",
    body_html: draft.body_html ?? null,
  };
}
