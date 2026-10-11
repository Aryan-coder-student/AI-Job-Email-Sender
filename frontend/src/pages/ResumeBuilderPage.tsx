import { useMutation, useQuery } from "@tanstack/react-query";
import { Download, FileCode2, RefreshCw, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";

import { api, type ResumeDocument } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Field, Input, Textarea } from "@/shared/ui/form";

export function ResumeBuilderPage() {
  const { data: profile, isLoading } = useQuery({ queryKey: ["resume-profile"], queryFn: api.resumeProfile });
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [description, setDescription] = useState("");
  const [document, setDocument] = useState<ResumeDocument | null>(null);
  const [source, setSource] = useState("");
  const [previewVersion, setPreviewVersion] = useState(0);

  const create = useMutation({
    mutationFn: api.createResumeDocument,
    onSuccess: async (value) => {
      setDocument(value);
      setSource(await fetch(api.resumeExportUrl(value.id, "source")).then((response) => response.text()));
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

  useEffect(() => { if (document?.custom_latex) setSource(document.custom_latex); }, [document]);

  if (isLoading) return <div className="text-sm text-muted-foreground">Loading resume profile…</div>;

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-bold">Resume Builder</h1>
        <p className="text-sm text-muted-foreground">Tailor {profile?.name || "your profile"} to a job, edit the generated LaTeX, and export it.</p>
      </div>
      <div className="grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="grid content-start gap-4">
          <Card>
            <CardHeader><CardTitle>Target job</CardTitle></CardHeader>
            <CardContent className="grid gap-3">
              <Field label="Company"><Input value={company} onChange={(e) => setCompany(e.target.value)} /></Field>
              <Field label="Role"><Input value={role} onChange={(e) => setRole(e.target.value)} /></Field>
              <Field label="Job description"><Textarea className="min-h-44" value={description} onChange={(e) => setDescription(e.target.value)} /></Field>
              <Field label="Existing LaTeX resume (optional)" hint="Leave empty to use JV's Resume Template, or paste an existing .tex source to preserve it.">
                <Textarea className="min-h-44 font-mono text-xs" value={source} onChange={(e) => setSource(e.target.value)} placeholder="JV's Resume Template will be used by default." />
              </Field>
              <Button disabled={!company || create.isPending} onClick={() => create.mutate({ company_name: company, role, description, source_latex: source || undefined })}>
                <Sparkles className="mr-2 h-4 w-4" />{create.isPending ? "Matching…" : "Build tailored resume"}
              </Button>
            </CardContent>
          </Card>
          {document ? <Card>
            <CardHeader><CardTitle>Recommended content</CardTitle></CardHeader>
            <CardContent className="grid gap-3">
              {document.recommendations.map((item) => <label key={item.item_id} className="flex gap-3 rounded-md border p-3 text-sm">
                <input type="checkbox" checked={document.selected_item_ids.includes(item.item_id)} onChange={(event) => {
                  const ids = event.target.checked ? [...document.selected_item_ids, item.item_id] : document.selected_item_ids.filter((id) => id !== item.item_id);
                  api.updateResumeDocument(document.id, { selected_item_ids: ids, custom_latex: null }).then(async (next) => {
                    setDocument(next); setSource(await fetch(api.resumeExportUrl(next.id, "source")).then((response) => response.text()));
                  });
                }} />
                <span><span className="font-semibold">{item.title}</span> · {Math.round(item.score * 100)}%<span className="block text-xs text-muted-foreground">{item.reason}</span></span>
              </label>)}
            </CardContent>
          </Card> : null}
        </div>
        <Card className="min-w-0">
          <CardHeader><CardTitle>Editor and live output</CardTitle></CardHeader>
          <CardContent className="grid gap-3">
            <div className="grid gap-3 xl:grid-cols-2">
              <div className="grid content-start gap-2">
                <span className="text-sm font-semibold">Editable LaTeX</span>
                <Textarea className="min-h-[620px] font-mono text-xs" disabled={!document} value={source} onChange={(e) => setSource(e.target.value)} placeholder="Generate a resume to begin editing." />
              </div>
              <div className="grid content-start gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold">Compiled résumé</span>
                  <Button size="sm" variant="ghost" disabled={!document} onClick={() => setPreviewVersion((version) => version + 1)}>
                    <RefreshCw className="h-4 w-4" />Refresh
                  </Button>
                </div>
                {document ? (
                  <iframe
                    key={previewVersion}
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
              <Button disabled={!document || save.isPending} onClick={() => save.mutate()}><FileCode2 className="mr-2 h-4 w-4" />Save, validate & preview</Button>
              {document ? <>
                <Button asChild variant="outline"><a href={api.resumeExportUrl(document.id, "source")}><Download className="mr-2 h-4 w-4" />LaTeX</a></Button>
                <Button asChild variant="outline"><a href={api.resumeExportUrl(document.id, "pdf")}><Download className="mr-2 h-4 w-4" />PDF</a></Button>
              </> : null}
            </div>
            {(create.error || save.error) ? <p className="text-sm text-destructive">{String(create.error || save.error)}</p> : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
