import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, FileCode2, RefreshCw, Sparkles, UserCheck } from "lucide-react";
import { useEffect, useState } from "react";

import { api, type ResumeDocument } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Field, Input, Textarea } from "@/shared/ui/form";

export function ResumeBuilderPage() {
  const queryClient = useQueryClient();
  const { data: profile, isLoading } = useQuery({ queryKey: ["resume-profile"], queryFn: api.resumeProfile });
  const { data: runs = [] } = useQuery({ queryKey: ["runs"], queryFn: api.listRuns });

  const [selectedRunId, setSelectedRunId] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [description, setDescription] = useState("");
  const [document, setDocument] = useState<ResumeDocument | null>(null);
  const [source, setSource] = useState("");
  const [previewVersion, setPreviewVersion] = useState(0);

  const importProfile = useMutation({
    mutationFn: (runId: string) => api.importResumeProfile(runId),
    onSuccess: (imported) => {
      queryClient.setQueryData(["resume-profile"], imported);
      const matchingRun = runs.find((r) => r.run_id === selectedRunId);
      if (matchingRun?.config.target_company && !company) {
        setCompany(String(matchingRun.config.target_company));
      }
    },
  });

  const create = useMutation({
    mutationFn: api.createResumeDocument,
    onSuccess: async (value) => {
      setDocument(value);
      if (value.custom_latex) {
        setSource(value.custom_latex);
      } else {
        const fetched = await fetch(api.resumeExportUrl(value.id, "source")).then((r) => r.text());
        setSource(fetched);
      }
      setPreviewVersion((version) => version + 1);
    },
  });

  const save = useMutation({
    mutationFn: () => api.updateResumeDocument(document!.id, { custom_latex: source }),
    onSuccess: (value) => {
      setDocument(value);
      setPreviewVersion((version) => version + 1);
    },
  });

  const updateSelection = useMutation({
    mutationFn: (ids: string[]) =>
      api.updateResumeDocument(document!.id, { selected_item_ids: ids, custom_latex: null }),
    onSuccess: async (next) => {
      setDocument(next);
      if (next.custom_latex) {
        setSource(next.custom_latex);
      } else {
        const fetched = await fetch(api.resumeExportUrl(next.id, "source")).then((r) => r.text());
        setSource(fetched);
      }
      setPreviewVersion((version) => version + 1);
    },
  });

  useEffect(() => {
    if (document?.custom_latex) setSource(document.custom_latex);
  }, [document]);

  const activeError =
    create.error || save.error || updateSelection.error || importProfile.error;

  const errorMessage = activeError
    ? activeError instanceof Error
      ? activeError.message
      : String(activeError)
    : null;

  if (isLoading) return <div className="text-sm text-muted-foreground">Loading resume profile…</div>;

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-bold">Resume Builder</h1>
        <p className="text-sm text-muted-foreground">
          Tailor {profile?.name || "your profile"} to a job, edit the generated LaTeX, and export it.
        </p>
      </div>

      {errorMessage ? (
        <div
          role="alert"
          className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive font-medium"
        >
          {errorMessage}
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="grid content-start gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Candidate profile</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                <select
                  aria-label="Select previous run"
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  value={selectedRunId}
                  onChange={(e) => setSelectedRunId(e.target.value)}
                >
                  <option value="">Select a previous run to import…</option>
                  {runs.map((r) => (
                    <option key={r.run_id} value={r.run_id}>
                      {r.run_id} {r.config.target_company ? `(${String(r.config.target_company)})` : ""}
                    </option>
                  ))}
                </select>
                <Button
                  type="button"
                  variant="outline"
                  disabled={!selectedRunId || importProfile.isPending}
                  onClick={() => selectedRunId && importProfile.mutate(selectedRunId)}
                >
                  <UserCheck className="mr-2 h-4 w-4" />
                  {importProfile.isPending ? "Importing…" : "Import"}
                </Button>
              </div>
              <div className="rounded-md border border-border p-3 text-sm">
                <span className="font-semibold block">{profile?.name || "No profile imported"}</span>
                {profile?.headline ? (
                  <span className="text-xs text-muted-foreground block">{profile.headline}</span>
                ) : null}
                <span className="text-xs text-muted-foreground block mt-1">
                  {profile?.projects?.length ?? 0} projects · {profile?.skills?.length ?? 0} skills
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Target job</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3">
              <Field label="Company">
                <Input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="e.g. Acme Corp" />
              </Field>
              <Field label="Role">
                <Input value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. Senior Backend Engineer" />
              </Field>
              <Field label="Job description">
                <Textarea
                  className="min-h-36"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Paste job requirements or description…"
                />
              </Field>
              <Field
                label="Existing LaTeX resume (optional)"
                hint="Leave empty to use JV's Resume Template, or paste an existing .tex source to preserve it."
              >
                <Textarea
                  className="min-h-36 font-mono text-xs"
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  placeholder="JV's Resume Template will be used by default."
                />
              </Field>
              <Button
                disabled={!company || create.isPending}
                onClick={() =>
                  create.mutate({
                    company_name: company,
                    role,
                    description,
                    source_latex: source || undefined,
                  })
                }
              >
                <Sparkles className="mr-2 h-4 w-4" />
                {create.isPending ? "Matching…" : "Build tailored resume"}
              </Button>
            </CardContent>
          </Card>

          {document ? (
            <Card>
              <CardHeader>
                <CardTitle>Recommended content</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3">
                {document.recommendations.map((item) => (
                  <label key={item.item_id} className="flex gap-3 rounded-md border p-3 text-sm cursor-pointer hover:bg-accent/40 transition-colors">
                    <input
                      type="checkbox"
                      aria-label={`Toggle recommendation ${item.title}`}
                      checked={document.selected_item_ids.includes(item.item_id)}
                      disabled={updateSelection.isPending}
                      onChange={(event) => {
                        const ids = event.target.checked
                          ? [...document.selected_item_ids, item.item_id]
                          : document.selected_item_ids.filter((id) => id !== item.item_id);
                        updateSelection.mutate(ids);
                      }}
                    />
                    <span>
                      <span className="font-semibold">{item.title}</span> · {Math.round(item.score * 100)}%
                      <span className="block text-xs text-muted-foreground">{item.reason}</span>
                    </span>
                  </label>
                ))}
              </CardContent>
            </Card>
          ) : null}
        </div>

        <Card className="min-w-0">
          <CardHeader>
            <CardTitle>Editor and live output</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            <div className="grid gap-3 xl:grid-cols-2">
              <div className="grid content-start gap-2">
                <span className="text-sm font-semibold">Editable LaTeX</span>
                <Textarea
                  aria-label="Editable LaTeX"
                  className="min-h-[620px] font-mono text-xs"
                  disabled={!document}
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  placeholder="Generate a resume to begin editing."
                />
              </div>
              <div className="grid content-start gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold">Compiled résumé</span>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={!document}
                    data-testid="refresh-preview-button"
                    aria-label="Refresh preview"
                    onClick={() => setPreviewVersion((version) => version + 1)}
                  >
                    <RefreshCw className="h-4 w-4 mr-1" />
                    Refresh
                  </Button>
                </div>
                {document ? (
                  <iframe
                    key={previewVersion}
                    data-testid="resume-preview-iframe"
                    title="Compiled resume preview"
                    className="h-[620px] w-full rounded-md border border-border bg-white"
                    src={`${api.resumeExportUrl(document.id, "pdf")}?v=${previewVersion}`}
                  />
                ) : (
                  <div className="grid h-[620px] place-items-center rounded-md border border-dashed border-border text-sm text-muted-foreground">
                    The compiled PDF will appear here.
                  </div>
                )}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button disabled={!document || save.isPending} onClick={() => save.mutate()}>
                <FileCode2 className="mr-2 h-4 w-4" />
                {save.isPending ? "Validating & saving…" : "Save, validate & preview"}
              </Button>
              {document ? (
                <>
                  <Button asChild variant="outline">
                    <a href={api.resumeExportUrl(document.id, "source")} download={`resume-${document.id}.tex`}>
                      <Download className="mr-2 h-4 w-4" />
                      LaTeX
                    </a>
                  </Button>
                  <Button asChild variant="outline">
                    <a href={api.resumeExportUrl(document.id, "pdf")} download={`resume-${document.id}.pdf`}>
                      <Download className="mr-2 h-4 w-4" />
                      PDF
                    </a>
                  </Button>
                </>
              ) : null}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

