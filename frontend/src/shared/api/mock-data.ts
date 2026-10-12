import type {
  CompanyRecord,
  EmailDraft,
  MailQueueResult,
  MatchResult,
  ParsedGitHubProfile,
  ParsedResume,
  PipelineRun,
  ResumeDocument,
  ResumeProfile,
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
    graph_score: 0,
    embedding_score: 0.032,
    llm_score: 0.015,
    final_score: 0.014,
    explanation: "Limited graph evidence, but shows production ML platform experience.",
    paths: [],
  },
];

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
  { draft_id: "demo-draft", to: "hr@example.com", status: "dry_run" },
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

export const mockResumeProfile: ResumeProfile = {
  name: "Aryan Pahari",
  headline: "Full-Stack & Systems Engineer",
  summary: "Experienced in building scalable backend services and AI agent pipelines.",
  email: "aryan@example.com",
  phone: "+1-555-0199",
  links: ["https://github.com/Aryan-coder-student"],
  skills: ["Python", "TypeScript", "FastAPI", "React", "Docker", "Neo4j"],
  experiences: [
    { id: "exp-1", title: "Software Engineer", subtitle: "Tech Labs", date: "2023 - Present", description: "Architected distributed pipeline and automation platform." },
  ],
  projects: [
    { id: "proj-1", title: "Job Send Crawl", description: "AI-assisted job outreach automation and knowledge graph matching.", skills: ["Python", "Neo4j", "Qdrant", "React"] },
    { id: "proj-2", title: "Resume Builder", description: "Automated LaTeX resume tailoring and compilation service.", skills: ["LaTeX", "Python", "FastAPI"] },
  ],
  education: [
    { id: "edu-1", title: "B.Tech Computer Science", subtitle: "University", date: "2019 - 2023" },
  ],
};

export const mockResumeDocument: ResumeDocument = {
  id: "doc-mock-123",
  company_name: "10up",
  role: "Backend Engineer",
  template: "jvs",
  section_order: ["summary", "skills", "experience", "projects", "education"],
  selected_item_ids: ["proj-1", "proj-2"],
  profile: mockResumeProfile,
  recommendations: [
    { item_id: "proj-1", section: "projects", title: "Job Send Crawl", score: 0.95, matched_keywords: ["Python", "FastAPI"], reason: "Matches Python and FastAPI backend requirements." },
    { item_id: "proj-2", section: "projects", title: "Resume Builder", score: 0.88, matched_keywords: ["LaTeX", "FastAPI"], reason: "Demonstrates API and templating capabilities." },
  ],
  custom_latex: "\\documentclass{article}\n\\begin{document}\nAryan Pahari\n\\end{document}",
};

