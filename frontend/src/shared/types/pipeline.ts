export type StepStatus = "pending" | "running" | "completed" | "failed" | "skipped";
export type RunStatus = "created" | "running" | "completed" | "failed";

export interface PipelineStepStatus {
  key: string;
  label: string;
  status: StepStatus;
  artifact_type?: ArtifactType | null;
  artifact_path?: string | null;
  summary?: string | null;
  error?: string | null;
}

export interface PipelineRun {
  run_id: string;
  status: RunStatus;
  created_at: string;
  updated_at: string;
  config: Record<string, unknown>;
  steps: PipelineStepStatus[];
  latest_error?: string | null;
  logs: string[];
}

export type ArtifactType = "resume" | "github" | "graph" | "matches" | "drafts" | "mail";

export interface SystemStatus {
  llm: {
    configured: boolean;
    providers: Record<
      string,
      {
        configured: boolean;
        key_count?: number;
        model?: string;
      }
    >;
  };
  services: Record<
    string,
    {
      configured: boolean;
      url?: string;
      provider?: string;
      from_email?: string;
    }
  >;
  dry_run_available: boolean;
}

export interface ResumeLinks {
  emails: string[];
  phones: string[];
  github?: string | null;
  linkedin?: string | null;
  portfolio?: string | null;
  urls: string[];
}

export interface ResumeExperience {
  company_name?: string | null;
  date?: string | null;
  description?: string | null;
}

export interface ResumeProject {
  project_name?: string | null;
  link?: string | null;
  description?: string | null;
}

export interface ParsedResume {
  filename?: string | null;
  file_extension: string;
  candidate_name?: string | null;
  summary: string;
  skills: string[];
  experience: ResumeExperience[];
  projects: ResumeProject[];
  achievements: string[];
  research: string[];
  education: string[];
  links: ResumeLinks;
  raw_text: string;
  metadata: Record<string, unknown>;
}

export interface ParsedGitHubProject {
  repo_name: string;
  repo_link: string;
  deployed_link?: string | null;
  summary: string;
  tech_stack: {
    backend: string[];
    frontend: string[];
    ai_ml: string[];
  };
  non_tech_tags: string[];
  raw_readme: string;
}

export interface ParsedGitHubProfile {
  github_username: string;
  github_url: string;
  projects: ParsedGitHubProject[];
  metadata: Record<string, unknown>;
}

export interface MatchResult {
  project_id: string;
  project_name: string;
  graph_score: number;
  embedding_score: number;
  llm_score: number;
  final_score: number;
  explanation: string;
  paths: unknown[];
}

export interface EmailDraft {
  draft_id: string;
  to: string;
  subject: string;
  body_text: string;
  body_html?: string | null;
  company_name: string;
  project_name?: string | null;
  status: "draft" | "queued" | "sent" | "failed" | "dry_run";
  metadata: Record<string, unknown>;
}

export type EmailDraftMap = Record<string, EmailDraft>;

export type DraftUpdatePayload = Pick<
  EmailDraft,
  "to" | "subject" | "body_text" | "body_html"
> & {
  company_name?: string;
};

export interface MailQueueResult {
  draft_id: string;
  to?: string | null;
  status: string;
}

export interface CompanyRecord {
  company_name?: string | null;
  role?: string | null;
  job_url?: string | null;
  company_url?: string | null;
  company_linkedin_url?: string | null;
  company_description?: string | null;
  hr_email?: string | null;
  contact_name?: string | null;
  source_sheet?: string | null;
  source_row?: number | null;
  raw_data?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface CompanyImportRow {
  row_id: string;
  source_sheet: string;
  source_row: number;
  normalized: CompanyRecord;
  raw_data: Record<string, unknown>;
  issues: string[];
  is_valid: boolean;
}

export interface CompanyImportPreview {
  import_id: string;
  filename: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  rows: CompanyImportRow[];
}

export interface NewRunFormValues {
  resume?: FileList;
  companies?: FileList;
  companies_url?: string;
  selected_companies?: CompanyRecord[];
  target_company?: string;
  recipient_email?: string;
  job_url?: string;
  header_row: number;
  sheet_names?: string;
  max_rows?: number;
  max_repos: number;
  max_companies: number;
  top_matches: number;
  dry_run: boolean;
  no_enqueue: boolean;
  skip_enrichment: boolean;
  skip_services: boolean;
  clear_graph: boolean;
}
