import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, CheckCircle2, FileSpreadsheet, FileText, Link2, Play } from "lucide-react";
import { useMemo, useState } from "react";
import { useForm, type UseFormReturn } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import { api } from "@/shared/api/client";
import { newRunSchema } from "@/shared/api/schemas";
import type {
  CompanyImportPreview,
  CompanyImportRow,
  NewRunFormValues,
} from "@/shared/types/pipeline";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { DataTable, Td, Th } from "@/shared/ui/data-table";
import { Field, Input } from "@/shared/ui/form";

const wizardSteps = ["Import", "Select", "Options", "Review"];

const defaultValues: NewRunFormValues = {
  target_company: "",
  recipient_email: "",
  job_url: "",
  companies_url: "",
  max_repos: 100,
  max_companies: 25,
  top_matches: 5,
  dry_run: true,
  no_enqueue: false,
  skip_enrichment: false,
  skip_services: false,
  clear_graph: false,
  selected_companies: [],
  header_row: 1,
  sheet_names: "",
};

export function NewRunWizard() {
  const [step, setStep] = useState(0);
  const [preview, setPreview] = useState<CompanyImportPreview | null>(null);
  const [selectedRowIds, setSelectedRowIds] = useState<Set<string>>(new Set());
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const form = useForm<NewRunFormValues>({
    resolver: zodResolver(newRunSchema),
    defaultValues,
  });
  const values = form.watch();
  const selectedRows = useMemo(
    () => preview?.rows.filter((row) => selectedRowIds.has(row.row_id)) ?? [],
    [preview, selectedRowIds],
  );
  const selectedCompanies = selectedRows.map((row) => row.normalized);

  const previewMutation = useMutation({
    mutationFn: (source: File | string) => api.previewCompanies(source, {
      header_row: values.header_row,
      sheet_names: values.sheet_names,
      max_rows: values.max_rows,
    }),
    onSuccess: (result) => {
      setPreview(result);
      setSelectedRowIds(new Set());
    },
  });
  const runMutation = useMutation({
    mutationFn: (payload: NewRunFormValues) =>
      api.createRun({
        ...payload,
        selected_companies: selectedCompanies,
      }),
    onSuccess: async (run) => {
      await queryClient.invalidateQueries({ queryKey: ["runs"] });
      navigate(`/runs/${run.run_id}`);
    },
  });

  const next = async () => {
    if (step === 0 && !preview) return;
    if (step === 1 && selectedCompanies.length === 0) return;

    if (step === 2) {
      const valid = await form.trigger(["recipient_email", "job_url", "max_repos", "max_companies", "top_matches"]);
      if (!valid) return;
    }

    setStep((current) => Math.min(current + 1, wizardSteps.length - 1));
  };

  const parseCompanies = () => {
    const source = companyImportSource(values);
    if (source) previewMutation.mutate(source);
  };

  const submitRun = form.handleSubmit((payload) => {
    runMutation.mutate({
      ...payload,
      selected_companies: selectedCompanies,
      target_company: "", // Removed manual target selection for batch
    });
  });

  return (
    <form className="grid gap-4" onSubmit={submitRun}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-2">
          {wizardSteps.map((label, index) => (
            <Button
              key={label}
              type="button"
              variant={index === step ? "default" : "outline"}
              onClick={() => setStep(index)}
            >
              {index + 1}. {label}
            </Button>
          ))}
        </div>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => setStep((current) => Math.max(current - 1, 0))}
          >
            Back
          </Button>
          {step < wizardSteps.length - 1 ? (
            <Button
              type="button"
              onClick={next}
              disabled={!canContinue(step, preview, selectedCompanies.length)}
            >
              Next
            </Button>
          ) : (
            <Button type="submit" disabled={runMutation.isPending || selectedCompanies.length === 0}>
              <Play className="h-4 w-4" />
              Start run
            </Button>
          )}
        </div>
      </div>

      {step === 0 ? (
        <ImportStep
          form={form}
          onParse={parseCompanies}
          preview={preview}
          isParsing={previewMutation.isPending}
          error={previewMutation.error}
        />
      ) : null}

      {step === 1 ? (
        <CompanySelectionStep
          preview={preview}
          selectedRowIds={selectedRowIds}
          onSelectionChange={(nextSet) => {
            setSelectedRowIds(nextSet);
          }}
        />
      ) : null}

      {step === 2 ? <OptionsStep form={form} /> : null}

      {step === 3 ? (
        <ReviewStep
          values={values}
          selectedRows={selectedRows}
          error={runMutation.error}
          formErrors={form.formState.errors}
        />
      ) : null}

    </form>
  );
}

function ImportStep({
  form,
  onParse,
  preview,
  isParsing,
  error,
}: {
  form: UseFormReturn<NewRunFormValues>;
  onParse: () => void;
  preview: CompanyImportPreview | null;
  isParsing: boolean;
  error: Error | null;
}) {
  const [sourceMode, setSourceMode] = useState<"file" | "url">("file");
  const companiesFile = form.watch("companies")?.[0];
  const companiesUrl = form.watch("companies_url")?.trim() ?? "";
  const canParseCompanies = sourceMode === "file" ? Boolean(companiesFile) : Boolean(companiesUrl);

  const switchMode = (mode: "file" | "url") => {
    setSourceMode(mode);
    if (mode === "url") {
      form.setValue("companies", undefined as unknown as FileList);
    } else {
      form.setValue("companies_url", "");
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Import files</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4">
        {/* Resume upload - always visible */}
        <Field label="Resume file" hint="Required before orchestration can run">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <Input type="file" accept=".pdf,.docx,.txt" {...form.register("resume")} />
          </div>
        </Field>

        {/* Company source toggle */}
        <div className="grid gap-3">
          <label className="text-sm font-semibold">Company source</label>
          <div className="flex gap-1 rounded-md border p-1 w-fit">
            <button
              type="button"
              className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${sourceMode === "file" ? "bg-primary text-primary-foreground" : "hover:bg-muted"}`}
              onClick={() => switchMode("file")}
            >
              Upload File
            </button>
            <button
              type="button"
              className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${sourceMode === "url" ? "bg-primary text-primary-foreground" : "hover:bg-muted"}`}
              onClick={() => switchMode("url")}
            >
              Google Sheet URL
            </button>
          </div>

          {sourceMode === "file" ? (
            <Field label="Companies file" hint="Excel, CSV, or JSON">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="h-4 w-4 text-muted-foreground" />
                <Input
                  type="file"
                  accept=".xlsx,.xlsm,.xltx,.xltm,.json,.csv"
                  {...form.register("companies")}
                />
              </div>
            </Field>
          ) : (
            <Field label="Google Sheet URL" hint="Paste your Google Sheets share link">
              <div className="flex items-center gap-2">
                <Link2 className="h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="https://docs.google.com/spreadsheets/d/..."
                  {...form.register("companies_url")}
                />
              </div>
            </Field>
          )}
        </div>

        {/* Parser settings */}
        <div className="grid gap-4 md:grid-cols-3">
          <Field label="Header row" hint="Row index containing column names (1-indexed)" error={form.formState.errors.header_row?.message}>
            <Input type="number" min={1} {...form.register("header_row", { valueAsNumber: true })} />
          </Field>
          <Field label="Target sheets" hint="Comma separated sheet names. Leave empty for first sheet." error={form.formState.errors.sheet_names?.message}>
            <Input placeholder="Sheet1, Sheet2" {...form.register("sheet_names")} />
          </Field>
          <Field label="Max rows" hint="Maximum rows to parse (optional)" error={form.formState.errors.max_rows?.message}>
            <Input type="number" min={1} placeholder="1000" {...form.register("max_rows", { valueAsNumber: true, setValueAs: (v) => v ? parseInt(v, 10) : undefined })} />
          </Field>
        </div>

        <div className="flex items-center gap-3">
          <Button type="button" onClick={onParse} disabled={!canParseCompanies || isParsing}>
            <FileSpreadsheet className="h-4 w-4" />
            {isParsing ? "Parsing..." : "Parse companies"}
          </Button>
          {preview ? (
            <Badge tone={preview.invalid_rows > 0 ? "amber" : "green"}>
              {preview.valid_rows}/{preview.total_rows} valid rows
            </Badge>
          ) : null}
        </div>
        {error ? (
          <p className="flex items-center gap-2 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            {error.message}
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}

function CompanySelectionStep({
  preview,
  selectedRowIds,
  onSelectionChange,
}: {
  preview: CompanyImportPreview | null;
  selectedRowIds: Set<string>;
  onSelectionChange: (next: Set<string>) => void;
}) {
  if (!preview) {
    return (
      <Card>
        <CardContent className="p-4 text-sm text-muted-foreground">
          Parse a company file before selecting rows.
        </CardContent>
      </Card>
    );
  }

  const toggleRow = (row: CompanyImportRow) => {
    const next = new Set(selectedRowIds);
    if (next.has(row.row_id)) next.delete(row.row_id);
    else next.add(row.row_id);
    onSelectionChange(next);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Company preview</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3">
        <div className="flex flex-wrap gap-2">
          <Badge tone="blue">{preview.filename}</Badge>
          <Badge tone="green">{preview.valid_rows} valid</Badge>
          <Badge tone={preview.invalid_rows ? "amber" : "neutral"}>{preview.invalid_rows} with issues</Badge>
        </div>
        <DataTable>
          <thead>
            <tr>
              <Th className="w-12">Use</Th>
              <Th>Company</Th>
              <Th>Role</Th>
              <Th>Contact</Th>
              <Th>Issues</Th>
            </tr>
          </thead>
          <tbody>
            {preview.rows.map((row) => (
              <tr key={row.row_id}>
                <Td>
                  <input
                    aria-label={`Select ${row.normalized.company_name ?? row.row_id}`}
                    checked={selectedRowIds.has(row.row_id)}
                    disabled={!row.is_valid}
                    type="checkbox"
                    onChange={() => toggleRow(row)}
                  />
                </Td>
                <Td>
                  <div className="font-semibold">{row.normalized.company_name ?? "Missing company"}</div>
                  <div className="text-xs text-muted-foreground">
                    {row.source_sheet} row {row.source_row}
                  </div>
                </Td>
                <Td>{row.normalized.role ?? "-"}</Td>
                <Td>{row.normalized.hr_email ?? "-"}</Td>
                <Td>
                  {row.issues.length ? (
                    <span className="text-destructive">{row.issues.join(", ")}</span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-emerald-700">
                      <CheckCircle2 className="h-4 w-4" />
                      Ready
                    </span>
                  )}
                </Td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </CardContent>
    </Card>
  );
}

function OptionsStep({ form }: { form: UseFormReturn<NewRunFormValues> }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Pipeline options</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-3">

        <Field label="Recipient email" error={form.formState.errors.recipient_email?.message}>
          <Input placeholder="hr@example.com" {...form.register("recipient_email")} />
        </Field>
        <Field label="Job URL" error={form.formState.errors.job_url?.message}>
          <Input placeholder="https://company.com/jobs/role" {...form.register("job_url")} />
        </Field>
        <Field label="Max GitHub repos" error={form.formState.errors.max_repos?.message}>
          <Input type="number" {...form.register("max_repos", { valueAsNumber: true })} />
        </Field>
        <Field label="Max companies" error={form.formState.errors.max_companies?.message}>
          <Input type="number" {...form.register("max_companies", { valueAsNumber: true })} />
        </Field>
        <Field label="Top matches" error={form.formState.errors.top_matches?.message}>
          <Input type="number" {...form.register("top_matches", { valueAsNumber: true })} />
        </Field>
        {[
          ["dry_run", "Dry run"],
          ["no_enqueue", "Do not enqueue"],
          ["skip_enrichment", "Skip enrichment"],
          ["skip_services", "Skip service wait"],
          ["clear_graph", "Clear graph"],
        ].map(([name, label]) => (
          <label key={name} className="flex items-center gap-2 text-sm font-semibold">
            <input type="checkbox" {...form.register(name as keyof NewRunFormValues)} />
            {label}
          </label>
        ))}
      </CardContent>
    </Card>
  );
}

function ReviewStep({
  values,
  selectedRows,
  error,
  formErrors,
}: {
  values: NewRunFormValues;
  selectedRows: CompanyImportRow[];
  error: Error | null;
  formErrors?: Record<string, any>;
}) {
  const review = {
    selected_companies: selectedRows.map((row) => row.normalized.company_name),
    dry_run: values.dry_run,
    no_enqueue: values.no_enqueue,
    skip_enrichment: values.skip_enrichment,
    skip_services: values.skip_services,
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Review run</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3">
        {formErrors && Object.keys(formErrors).length > 0 ? (
          <div className="rounded-md bg-destructive/10 p-4 text-sm text-destructive">
            <h4 className="font-semibold mb-2 flex items-center gap-2">
              Please fix the following errors before starting:
            </h4>
            <ul className="list-disc pl-5">
              {Object.entries(formErrors).map(([field, err]) => (
                <li key={field}>
                  <span className="font-semibold capitalize">{field.replace("_", " ")}:</span> {err?.message as string}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        <pre className="overflow-auto rounded-md bg-muted p-3 text-xs">
          {JSON.stringify(review, null, 2)}
        </pre>
        {error ? <p className="text-sm text-destructive">{error.message}</p> : null}
      </CardContent>
    </Card>
  );
}

function companyImportSource(values: NewRunFormValues): File | string | null {
  const companiesUrl = values.companies_url?.trim();
  if (companiesUrl) return companiesUrl;

  return values.companies?.[0] ?? null;
}

function canContinue(
  step: number,
  preview: CompanyImportPreview | null,
  selectedCompanyCount: number,
) {
  if (step === 0) return Boolean(preview);
  if (step === 1) return selectedCompanyCount > 0;
  return true;
}
