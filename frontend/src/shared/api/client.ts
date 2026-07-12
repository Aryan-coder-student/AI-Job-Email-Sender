import {
  mockDraft,
  mockGithub,
  mockMail,
  mockMatches,
  mockCompanies,
  mockResume,
  mockRun,
  mockSystemStatus,
} from "@/shared/api/mock-data";
import type {
  ArtifactType,
  CompanyImportPreview,
  CompanyRecord,
  EmailDraft,
  EmailDraftMap,
  MailQueueResult,
  MatchResult,
  NewRunFormValues,
  ParsedGitHubProfile,
  ParsedResume,
  PipelineRun,
  SystemStatus,
} from "@/shared/types/pipeline";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public payload?: unknown,
  ) {
    super(message);
  }
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "/api/v1";
const useMocks = import.meta.env.VITE_USE_MOCKS === "true";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: init?.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...init,
  });

  if (!response.ok) {
    let payload: unknown;
    try {
      const text = await response.text();
      payload = text ? JSON.parse(text) : undefined;
    } catch {
      payload = undefined;
    }
    throw new ApiError(errorMessage(payload), response.status, payload);
  }

  return response.json() as Promise<T>;
}

function formDataFromRun(values: NewRunFormValues) {
  const formData = new FormData();
  const resume = values.resume?.[0];
  const companies = values.companies?.[0];

  if (resume) formData.append("resume", resume);
  if (companies) formData.append("companies", companies);
  if (values.header_row !== undefined && !Number.isNaN(values.header_row)) formData.append("header_row", String(values.header_row));
  if (values.sheet_names) formData.append("sheet_names", values.sheet_names);
  if (values.max_rows !== undefined && !Number.isNaN(values.max_rows)) formData.append("max_rows", String(values.max_rows));

  for (const [key, value] of Object.entries(values)) {
    if (key === "resume" || key === "companies" || key === "header_row" || key === "sheet_names" || key === "max_rows" || value === undefined) continue;
    if (key === "selected_companies") {
      formData.append("selected_companies", JSON.stringify(value));
      continue;
    }
    formData.append(key, String(value));
  }

  return formData;
}

function formDataFromCompanySource(source: File | string) {
  const formData = new FormData();
  if (typeof source === "string") {
    formData.append("companies_url", source);
    return formData;
  }

  formData.append("companies", source);
  return formData;
}

export const api = {
  async systemStatus(): Promise<SystemStatus> {
    if (useMocks) return mockSystemStatus;
    return request<SystemStatus>("/system/status");
  },
  async listRuns(): Promise<PipelineRun[]> {
    if (useMocks) return [mockRun];
    return request<PipelineRun[]>("/runs");
  },
  async createRun(values: NewRunFormValues): Promise<PipelineRun> {
    if (useMocks) return { ...mockRun, status: "created" };
    return request<PipelineRun>("/runs", {
      method: "POST",
      body: formDataFromRun(values),
    });
  },
  async previewCompanies(source: File | string, config?: { header_row?: number, sheet_names?: string, max_rows?: number }): Promise<CompanyImportPreview> {
    if (useMocks) {
      return {
        import_id: "mock-import",
        filename: typeof source === "string" ? source : source.name,
        total_rows: mockCompanies.length,
        valid_rows: mockCompanies.length,
        invalid_rows: 0,
        rows: mockCompanies.map((company, index) => ({
          row_id: `mock:${index + 1}`,
          source_sheet: "mock",
          source_row: index + 1,
          normalized: company,
          raw_data: company,
          issues: [],
          is_valid: true,
        })),
      };
    }
    const formData = formDataFromCompanySource(source);
    if (config?.header_row !== undefined && !Number.isNaN(config.header_row)) formData.append("header_row", String(config.header_row));
    if (config?.sheet_names) formData.append("sheet_names", config.sheet_names);
    if (config?.max_rows !== undefined && !Number.isNaN(config.max_rows)) formData.append("max_rows", String(config.max_rows));
    
    return request<CompanyImportPreview>("/runs/companies/preview", {
      method: "POST",
      body: formData,
    });
  },
  async getRun(runId: string): Promise<PipelineRun> {
    if (useMocks) return mockRun;
    return request<PipelineRun>(`/runs/${runId}`);
  },
  async retryRun(runId: string): Promise<PipelineRun> {
    if (useMocks) return { ...mockRun, status: "running" };
    return request<PipelineRun>(`/runs/${runId}/retry`, { method: "POST" });
  },
  async resumeRun(runId: string, fromStep?: string): Promise<PipelineRun> {
    if (useMocks) return { ...mockRun, status: "running" };
    return request<PipelineRun>(`/runs/${runId}/resume`, {
      method: "POST",
      body: JSON.stringify({ from_step: fromStep }),
    });
  },
  async artifact<T>(runId: string, artifactType: ArtifactType): Promise<T> {
    if (useMocks) return mockArtifact<T>(artifactType);
    return request<T>(`/runs/${runId}/artifacts/${artifactType}`);
  },
  async companies(runId: string): Promise<CompanyRecord[]> {
    if (useMocks) return mockCompanies;
    return request<CompanyRecord[]>(`/runs/${runId}/companies`);
  },
  async updateDraft(
    runId: string,
    companyName: string,
    draft: Pick<EmailDraft, "to" | "subject" | "body_text" | "body_html">,
  ): Promise<EmailDraftMap> {
    if (useMocks) return { [companyName]: { ...mockDraft, company_name: companyName, ...draft } };
    return request<EmailDraftMap>(`/runs/${runId}/drafts`, {
      method: "PUT",
      body: JSON.stringify({ company_name: companyName, ...draft }),
    });
  },
  async enqueueDraft(runId: string): Promise<EmailDraftMap> {
    if (useMocks) return { [mockDraft.company_name]: { ...mockDraft, status: "queued" as const } };
    return request<EmailDraftMap>(`/runs/${runId}/drafts/enqueue`, { method: "POST" });
  },
  async processMail(runId: string, payload: { dry_run: boolean; limit: number }) {
    if (useMocks) return mockMail;
    return request<MailQueueResult[]>(`/runs/${runId}/mail/process`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};

function errorMessage(payload: unknown) {
  if (typeof payload === "object" && payload && "detail" in payload) {
    return String((payload as { detail: unknown }).detail);
  }

  if (typeof payload === "string" && payload.trim()) {
    return payload;
  }

  return "API request failed.";
}

function mockArtifact<T>(artifactType: ArtifactType): T {
  const artifacts: Record<ArtifactType, unknown> = {
    resume: mockResume satisfies ParsedResume,
    github: mockGithub satisfies ParsedGitHubProfile,
    graph: {},
    matches: mockMatches satisfies MatchResult[],
    drafts: { [mockDraft.company_name]: mockDraft } satisfies EmailDraftMap,
    mail: mockMail satisfies MailQueueResult[],
  };
  return artifacts[artifactType] as T;
}
