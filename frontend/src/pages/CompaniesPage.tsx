import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, ExternalLink, Save } from "lucide-react";
import { useMemo, useState, useEffect } from "react";

import { useActiveRun } from "@/features/runs/hooks";
import { api } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input, Textarea, Field } from "@/shared/ui/form";
import { ProgressScore } from "@/shared/ui/progress-score";
import type { CompanyRecord, MatchResult, EmailDraft } from "@/shared/types/pipeline";

export function CompaniesPage() {
  const [query, setQuery] = useState("");
  const { runId } = useActiveRun();
  
  const { data: companies = [], isLoading: isLoadingCompanies } = useQuery({
    queryKey: ["companies", runId],
    queryFn: () => api.companies(runId),
  });
  const { data: matchesData, isLoading: isLoadingMatches } = useQuery({
    queryKey: ["artifact", runId, "matches"],
    queryFn: () => api.artifact<Record<string, MatchResult[]>>(runId, "matches"),
  });
  const { data: draftsData, isLoading: isLoadingDrafts } = useQuery({
    queryKey: ["artifact", runId, "drafts"],
    queryFn: () => api.artifact<Record<string, EmailDraft>>(runId, "drafts"),
  });

  const filteredCompanies = useMemo(
    () =>
      companies.filter((company) =>
        JSON.stringify(company).toLowerCase().includes(query.toLowerCase()),
      ),
    [companies, query],
  );

  const isLoading = isLoadingCompanies || isLoadingMatches || isLoadingDrafts;

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Companies Dashboard</h1>
        <p className="text-sm text-muted-foreground">Review company data, matches, and edit mail drafts.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Company records</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3">
          <Input placeholder="Search companies..." value={query} onChange={(event) => setQuery(event.target.value)} />
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading companies data...</p>
          ) : (
            <div className="grid gap-3">
              {filteredCompanies.map((company, index) => (
                <CompanyDashboardSection
                  key={`${company.company_name}-${index}`}
                  runId={runId}
                  company={company}
                  matches={matchesData && typeof matchesData === "object" && !Array.isArray(matchesData) && company.company_name ? (matchesData[company.company_name] || []) : []}
                  draft={draftsData && typeof draftsData === "object" && !Array.isArray(draftsData) && company.company_name ? draftsData[company.company_name] : undefined}
                />
              ))}
              {filteredCompanies.length === 0 && (
                <p className="text-sm text-muted-foreground">No companies found.</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function CompanyDashboardSection({ 
  runId,
  company, 
  matches, 
  draft 
}: { 
  runId: string;
  company: CompanyRecord; 
  matches: MatchResult[]; 
  draft?: EmailDraft;
}) {
  const [open, setOpen] = useState(false);
  const companyName = company.company_name ?? "Unknown";

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
        <div className="flex items-center gap-2">
          {draft && <span className="rounded-full bg-primary/10 text-primary px-2 py-0.5 text-xs font-medium">Draft: {draft.status ?? "draft"}</span>}
          <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium">
            {matches.length} matches
          </span>
        </div>
      </button>
      {open ? (
        <div className="border-t p-4 grid gap-6">
          {/* Company Info */}
          <div>
            <h3 className="font-semibold text-base mb-2">Company Information</h3>
            <div className="grid sm:grid-cols-2 gap-4 text-sm">
              <div><span className="text-muted-foreground">Role:</span> {company.role ?? "-"}</div>
              <div><span className="text-muted-foreground">Contact:</span> {company.contact_name ?? "-"} ({company.hr_email ?? "-"})</div>
              <div className="sm:col-span-2">
                <span className="text-muted-foreground">Description:</span> {company.company_description ?? "-"}
              </div>
              <div className="sm:col-span-2 flex gap-2">
                {company.job_url || company.company_url ? (
                  <Button asChild size="sm" variant="outline">
                    <a href={String(company.job_url || company.company_url)} target="_blank" rel="noreferrer">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Open Company Link
                    </a>
                  </Button>
                ) : null}
              </div>
            </div>
          </div>

          {/* Matches Info */}
          {matches.length > 0 && (
            <div>
              <h3 className="font-semibold text-base mb-2">Matched Projects</h3>
              <div className="grid gap-3">
                {matches.map((match) => (
                  <div key={match.project_id} className="rounded border p-3 bg-muted/20">
                    <div className="font-semibold mb-1">{match.project_name}</div>
                    <p className="text-xs text-muted-foreground mb-3">{match.explanation}</p>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      <ProgressScore label="Final" value={match.final_score} />
                      <ProgressScore label="Graph" value={match.graph_score} />
                      <ProgressScore label="Embedding" value={match.embedding_score} />
                      <ProgressScore label="LLM" value={match.llm_score} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Email Draft Edit Form */}
          {draft && (
            <div>
              <h3 className="font-semibold text-base mb-2">Email Draft</h3>
              <DraftEditor runId={runId} companyName={companyName} draft={draft} />
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}

function DraftEditor({ runId, companyName, draft }: { runId: string, companyName: string, draft: EmailDraft }) {
  const queryClient = useQueryClient();
  const [to, setTo] = useState(draft.to ?? "");
  const [subject, setSubject] = useState(draft.subject ?? "");
  const [bodyText, setBodyText] = useState(draft.body_text ?? "");
  
  useEffect(() => {
    setTo(draft.to ?? "");
    setSubject(draft.subject ?? "");
    setBodyText(draft.body_text ?? "");
  }, [draft]);

  const updateDraft = useMutation({
    mutationFn: () => api.updateDraft(runId, { company_name: companyName, to, subject, body_text: bodyText }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["artifact", runId, "drafts"] });
    },
  });

  return (
    <div className="grid gap-3">
      <Field label="To">
        <Input value={to} onChange={(e) => setTo(e.target.value)} />
      </Field>
      <Field label="Subject">
        <Input value={subject} onChange={(e) => setSubject(e.target.value)} />
      </Field>
      <Field label="Body">
        <Textarea 
          value={bodyText} 
          onChange={(e) => setBodyText(e.target.value)} 
          className="min-h-60 font-mono text-xs" 
        />
      </Field>
      <div className="flex justify-end gap-2 mt-2">
        <Button 
          size="sm" 
          onClick={() => updateDraft.mutate()}
          disabled={updateDraft.isPending}
        >
          <Save className="h-4 w-4 mr-2" />
          {updateDraft.isPending ? "Saving..." : "Save Draft"}
        </Button>
      </div>
      {updateDraft.isSuccess && <p className="text-xs text-green-600 text-right">Draft saved successfully.</p>}
      {updateDraft.isError && <p className="text-xs text-destructive text-right">Failed to save draft.</p>}
    </div>
  );
}
