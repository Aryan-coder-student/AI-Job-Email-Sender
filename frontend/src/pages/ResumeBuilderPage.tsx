import { useMutation, useQuery } from "@tanstack/react-query";
import { Download, FileCode2, Sparkles } from "lucide-react";
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

  const create = useMutation({
    mutationFn: api.createResumeDocument,
    onSuccess: async (value) => {
      setDocument(value);
      setSource(await fetch(api.resumeExportUrl(value.id, "source")).then((response) => response.text()));
    },
  });
  const save = useMutation({
    mutationFn: () => api.updateResumeDocument(document!.id, { custom_latex: source }),
    onSuccess: setDocument,
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
              <Field label="Existing LaTeX resume" hint="Paste the complete generated .tex source. Its formatting is preserved.">
                <Textarea className="min-h-44 font-mono text-xs" value={source} onChange={(e) => setSource(e.target.value)} placeholder="\\documentclass{...} ..." />
              </Field>
              <Button disabled={!company || !source.includes("\\begin{document}") || create.isPending} onClick={() => create.mutate({ company_name: company, role, description, source_latex: source })}>
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
          <CardHeader><CardTitle>LaTeX editor</CardTitle></CardHeader>
          <CardContent className="grid gap-3">
            <Textarea className="min-h-[560px] font-mono text-xs" disabled={!document} value={source} onChange={(e) => setSource(e.target.value)} placeholder="Generate a resume to begin editing." />
            <div className="flex flex-wrap gap-2">
              <Button disabled={!document || save.isPending} onClick={() => save.mutate()}><FileCode2 className="mr-2 h-4 w-4" />Save & validate</Button>
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
