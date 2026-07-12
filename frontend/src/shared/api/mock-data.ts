import type {
  CompanyRecord,
  EmailDraft,
  GraphArtifact,
  MailQueueResult,
  MatchResult,
  ParsedGitHubProfile,
  ParsedResume,
  PipelineRun,
  SystemStatus,
} from "@/shared/types/pipeline";

export const mockRun: PipelineRun = {
  run_id: "local-demo",
  status: "completed",
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  config: {
    target_company: "10up",
    dry_run: true,
  },
  latest_error: null,
  logs: ["Loaded existing artifacts.", "Pipeline completed."],
  steps: [
    { key: "parse_resume", label: "Parse Resume", status: "completed", artifact_type: "resume", summary: "ARYAN PAHARI" },
    { key: "parse_github", label: "Parse GitHub", status: "completed", artifact_type: "github", summary: "4 GitHub projects" },
    { key: "build_graph", label: "Build Graph + Vectors", status: "completed", artifact_type: "graph", summary: "Graph build artifact" },
    { key: "rank_projects", label: "Rank Projects", status: "completed", artifact_type: "matches", summary: "5 ranked matches" },
    { key: "generate_draft", label: "Generate Draft", status: "completed", artifact_type: "drafts", summary: "Application for Role at 10up" },
    { key: "process_mail_queue", label: "Process Mail Queue", status: "completed", artifact_type: "mail", summary: "1 mail result" },
  ],
};

export const mockSystemStatus: SystemStatus = {
  llm: {
    configured: true,
    providers: {
      groq: { configured: true, key_count: 2, model: "llama-3.3-70b-versatile" },
      openai: { configured: false, model: "default" },
      gemini: { configured: false, model: "default" },
    },
  },
  services: {
    redis: { configured: true, url: "redis://localhost:6379/2" },
    neo4j: { configured: true, url: "bolt://localhost:7687" },
    qdrant: { configured: true, url: "http://localhost:6333" },
    mail: { configured: false, provider: "gmail" },
    github: { configured: true },
  },
  dry_run_available: true,
};

export const mockResume: ParsedResume = {
  filename: "AryanPahari.pdf",
  file_extension: ".pdf",
  candidate_name: "ARYAN PAHARI",
  summary: "Backend and AI engineer building Python APIs, MLOps workflows, and LLM tools.",
  skills: ["Python", "FastAPI", "PostgreSQL", "LangChain", "Docker", "Redis"],
  experience: [
    {
      company_name: "omnisavant.ai",
      date: "12/2025 - 04/2026",
      description: "Built scalable FastAPI and Django REST APIs with Celery, Redis, PostgreSQL, and AWS.",
    },
  ],
  projects: [
    {
      project_name: "NeuroVision",
      link: "https://github.com/Aryan-coder-student/NeuroVision-BHPC",
      description: "Visual question answering and segmentation system for radiology workflows.",
    },
  ],
  achievements: ["Secured 9th place out of 267 teams in Health Hack Hackathon."],
  research: [],
  education: ["VIT Bhopal, B.Tech CSE AI-ML"],
  links: {
    emails: ["pahariaryan121@gmail.com"],
    phones: ["+91 9755530104"],
    github: "https://github.com/Aryan-coder-student",
    linkedin: "https://www.linkedin.com/in/aryanpahari037/",
    portfolio: "https://porfolio-ten-indol.vercel.app/",
    urls: [],
  },
  raw_text: "Raw resume text...",
  metadata: { llm_provider: "groq-1" },
};

export const mockGithub: ParsedGitHubProfile = {
  github_username: "Aryan-coder-student",
  github_url: "https://github.com/Aryan-coder-student",
  metadata: { repos_parsed: 4 },
  projects: [
    {
      repo_name: "AgroScan_Pro",
      repo_link: "https://github.com/Aryan-coder-student/AgroScan_Pro",
      deployed_link: "https://oraj131407-agroscan-dashboard.hf.space",
      summary: "Multi-tenant MLOps platform for precision agriculture and livestock monitoring.",
      tech_stack: {
        backend: ["FastAPI", "PyTorch", "SQLAlchemy"],
        frontend: ["React", "TypeScript", "Tailwind CSS"],
        ai_ml: ["Machine Learning", "Hugging Face"],
      },
      non_tech_tags: ["Precision Agriculture", "Livestock Monitoring"],
      raw_readme: "README...",
    },
  ],
};

export const mockMatches: MatchResult[] = [
  {
    project_id: "project:1",
    project_name: "Sentimental-analysis",
    graph_score: 0,
    embedding_score: 0.051,
    llm_score: 0.05,
    final_score: 0.03,
    explanation: "Low project-company fit due to limited direct relevance.",
    paths: [],
  },
  {
    project_id: "project:2",
    project_name: "AgroScan_Pro",
    graph_score: 0.34,
    embedding_score: 0.032,
    llm_score: 0.015,
    final_score: 0.15,
    explanation: "Strong project-company overlap across ML operations and domain signals.",
    paths: [
      {
        company_name: "10up",
        project_name: "AgroScan_Pro",
        path_labels: ["Company", "LOOKS_FOR", "Capability", "DEMONSTRATES", "Project"],
        graph_score: 0.34,
        match_source: "company_capability",
      },
    ],
  },
];

export const mockGraph: GraphArtifact = {
  candidate: {
    nodes_upserted: 24,
    edges_upserted: 41,
    metadata: { candidate_id: "candidate:aryan-coder-student" },
  },
  companies: {
    nodes_upserted: 88,
    edges_upserted: 134,
    metadata: { company_count: 12 },
  },
  vector_index: {
    projects_indexed: 8,
    jobs_indexed: 12,
  },
};

export const mockDraft: EmailDraft = {
  draft_id: "demo-draft",
  to: "hr@example.com",
  subject: "Application for Role at 10up",
  body_text:
    "Dear Hiring Manager, I am excited to apply for a role at 10up. My backend and AI experience can support your engineering team.",
  body_html: null,
  company_name: "10up",
  project_name: "Sentimental-analysis",
  status: "queued",
  metadata: { llm_provider: "groq-3", top_match: mockMatches[0] },
};

export const mockMail: MailQueueResult[] = [
  { draft_id: "demo-draft", to: "hr@example.com", status: "dry_run", provider: "gmail" },
];

export const mockCompanies: CompanyRecord[] = [
  {
    company_name: "10up",
    role: "Backend Engineer",
    company_url: "https://10up.com",
    job_url: "https://10up.com/careers",
    hr_email: "hr@example.com",
    company_description: "Creates finely crafted tools and websites for content creators.",
    source_sheet: "companies",
    source_row: 2,
  },
];
