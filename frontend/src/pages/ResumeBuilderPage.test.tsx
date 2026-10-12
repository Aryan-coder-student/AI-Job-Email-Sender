import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { PipelineRun, ResumeDocument, ResumeProfile } from "@/shared/types/pipeline";

vi.mock("@/shared/api/client", () => ({
  api: {
    listRuns: vi.fn(),
    resumeProfile: vi.fn(),
    importResumeProfile: vi.fn(),
    createResumeDocument: vi.fn(),
    updateResumeDocument: vi.fn(),
    companyResumes: vi.fn(),
    generateCompanyResumes: vi.fn(),
    getCompanyResume: vi.fn(),
    updateCompanyResume: vi.fn(),
    companyResumeExportUrl: vi.fn((run: string, key: string, format: string) => `/api/v1/resume-builder/runs/${run}/companies/${key}/${format}`),
    resumeExportUrl: vi.fn((id: string, format: string) => `/api/v1/resume-builder/documents/${id}/${format}`),
  },
}));

import { api } from "@/shared/api/client";
import { ResumeBuilderPage } from "@/pages/ResumeBuilderPage";

const mockProfile: ResumeProfile = {
  name: "Jane Developer",
  headline: "Full-Stack Engineer",
  summary: "Experienced software engineer",
  skills: ["React", "TypeScript", "Python"],
  projects: [{ id: "proj-1", title: "Project Alpha", description: "Alpha project", skills: ["Python"] }],
};

const mockRuns: PipelineRun[] = [
  {
    run_id: "run-demo-1",
    status: "completed",
    created_at: "2026-07-11T00:00:00.000Z",
    updated_at: "2026-07-11T00:00:00.000Z",
    config: { target_company: "Acme Corp" },
    steps: [],
    logs: [],
  },
];

const mockDocument: ResumeDocument = {
  id: "doc-123",
  company_name: "Acme Corp",
  role: "Backend Engineer",
  template: "jvs",
  section_order: ["summary", "skills", "projects"],
  selected_item_ids: ["proj-1"],
  profile: mockProfile,
  recommendations: [
    {
      item_id: "proj-1",
      section: "projects",
      title: "Project Alpha",
      score: 0.9,
      matched_keywords: ["Python"],
      reason: "Matches Python backend requirements",
    },
  ],
  custom_latex: "\\documentclass{article}\\begin{document}Jane Developer\\end{document}",
};

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ResumeBuilderPage />
    </QueryClientProvider>,
  );
}

describe("ResumeBuilderPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.resumeProfile).mockResolvedValue(mockProfile);
    vi.mocked(api.listRuns).mockResolvedValue(mockRuns);
    vi.mocked(api.companyResumes).mockResolvedValue({});
  });

  it("renders profile details and job inputs", async () => {
    renderPage();

    expect(await screen.findByText("Jane Developer")).toBeInTheDocument();
    expect(screen.getByText("Full-Stack Engineer")).toBeInTheDocument();
    expect(screen.getByLabelText("Company")).toBeInTheDocument();
    expect(screen.getByLabelText("Role")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Build tailored resume/i })).toBeInTheDocument();
  });

  it("handles API failure when building tailored resume and displays error message", async () => {
    const user = userEvent.setup();
    vi.mocked(api.createResumeDocument).mockRejectedValueOnce(new Error("LaTeX compilation server unavailable."));

    renderPage();
    await screen.findByText("Jane Developer");

    await user.type(screen.getByLabelText("Company"), "Acme Corp");
    await user.click(screen.getByRole("button", { name: /Build tailored resume/i }));

    const errorAlert = await screen.findByRole("alert");
    expect(errorAlert).toHaveTextContent("LaTeX compilation server unavailable.");
  });

  it("handles API failure when saving custom LaTeX and displays error message", async () => {
    const user = userEvent.setup();
    vi.mocked(api.createResumeDocument).mockResolvedValueOnce(mockDocument);
    vi.mocked(api.updateResumeDocument).mockRejectedValueOnce(new Error("LaTeX has unbalanced braces."));

    renderPage();
    await screen.findByText("Jane Developer");

    await user.type(screen.getByLabelText("Company"), "Acme Corp");
    await user.click(screen.getByRole("button", { name: /Build tailored resume/i }));

    await screen.findByText("Project Alpha");
    const saveButton = screen.getByRole("button", { name: /Save, validate & preview/i });
    await user.click(saveButton);

    const errorAlert = await screen.findByRole("alert");
    expect(errorAlert).toHaveTextContent("LaTeX has unbalanced braces.");
  });

  it("handles API failure when updating recommendation selection and displays error message", async () => {
    const user = userEvent.setup();
    vi.mocked(api.createResumeDocument).mockResolvedValueOnce(mockDocument);
    vi.mocked(api.updateResumeDocument).mockRejectedValueOnce(new Error("Failed to update recommendations."));

    renderPage();
    await screen.findByText("Jane Developer");

    await user.type(screen.getByLabelText("Company"), "Acme Corp");
    await user.click(screen.getByRole("button", { name: /Build tailored resume/i }));

    const checkbox = await screen.findByRole("checkbox", { name: /Toggle recommendation Project Alpha/i });
    expect(checkbox).toBeChecked();

    await user.click(checkbox);

    const errorAlert = await screen.findByRole("alert");
    expect(errorAlert).toHaveTextContent("Failed to update recommendations.");
  });

  it("refreshes the preview iframe URL when clicking the refresh button", async () => {
    const user = userEvent.setup();
    vi.mocked(api.createResumeDocument).mockResolvedValueOnce(mockDocument);

    renderPage();
    await screen.findByText("Jane Developer");

    await user.type(screen.getByLabelText("Company"), "Acme Corp");
    await user.click(screen.getByRole("button", { name: /Build tailored resume/i }));

    const iframe = (await screen.findByTestId("resume-preview-iframe")) as HTMLIFrameElement;
    expect(iframe.src).toContain("/api/v1/resume-builder/documents/doc-123/pdf?v=1");

    const refreshButton = screen.getByTestId("refresh-preview-button");
    await user.click(refreshButton);

    const updatedIframe = (await screen.findByTestId("resume-preview-iframe")) as HTMLIFrameElement;
    expect(updatedIframe.src).toContain("/api/v1/resume-builder/documents/doc-123/pdf?v=2");
  });

  it("updates selection and re-renders when toggling recommendation checkbox", async () => {
    const user = userEvent.setup();
    vi.mocked(api.createResumeDocument).mockResolvedValueOnce(mockDocument);
    const updatedDocument: ResumeDocument = {
      ...mockDocument,
      selected_item_ids: [],
      custom_latex: "\\documentclass{article}\\begin{document}Updated without Project Alpha\\end{document}",
    };
    vi.mocked(api.updateResumeDocument).mockResolvedValueOnce(updatedDocument);

    renderPage();
    await screen.findByText("Jane Developer");

    await user.type(screen.getByLabelText("Company"), "Acme Corp");
    await user.click(screen.getByRole("button", { name: /Build tailored resume/i }));

    const checkbox = await screen.findByRole("checkbox", { name: /Toggle recommendation Project Alpha/i });
    expect(checkbox).toBeChecked();

    await user.click(checkbox);

    expect(api.updateResumeDocument).toHaveBeenCalledWith("doc-123", {
      selected_item_ids: [],
      custom_latex: null,
    });

    await waitFor(() => {
      const textarea = screen.getByLabelText("Editable LaTeX") as HTMLTextAreaElement;
      expect(textarea.value).toContain("Updated without Project Alpha");
    });
  });

  it("opens a matched company resume using its run-scoped export and saves independently", async () => {
    const user = userEvent.setup();
    vi.mocked(api.companyResumes).mockResolvedValueOnce({
      "Acme Corp": { company_name: "Acme Corp", company_key: "acme-key", document_id: "doc-123", role: "Backend Engineer", match_count: 2, status: "ready" },
    });
    vi.mocked(api.getCompanyResume).mockResolvedValueOnce(mockDocument);
    vi.mocked(api.updateCompanyResume).mockResolvedValueOnce(mockDocument);
    renderPage();
    await screen.findByText("Jane Developer");
    await user.selectOptions(screen.getByLabelText("Select previous run"), "run-demo-1");
    await screen.findByText("Acme Corp");
    await user.click(screen.getByRole("button", { name: "Open" }));
    await screen.findByRole("checkbox", { name: /Toggle recommendation Project Alpha/ });
    const iframe = screen.getByTestId("resume-preview-iframe") as HTMLIFrameElement;
    expect(iframe.src).toContain("/runs/run-demo-1/companies/acme-key/pdf");
    await user.click(screen.getByRole("button", { name: /Save, validate & preview/i }));
    expect(api.updateCompanyResume).toHaveBeenCalledWith("run-demo-1", "acme-key", { custom_latex: mockDocument.custom_latex });
  });

  it("imports candidate profile from a previous run", async () => {
    const user = userEvent.setup();
    const importedProfile: ResumeProfile = {
      name: "Imported Candidate",
      headline: "DevOps Engineer",
      skills: ["Kubernetes", "Terraform"],
      projects: [],
    };
    vi.mocked(api.importResumeProfile).mockResolvedValueOnce(importedProfile);

    renderPage();
    await screen.findByText("Jane Developer");

    const select = screen.getByLabelText("Select previous run");
    await user.selectOptions(select, "run-demo-1");

    const importButton = screen.getByRole("button", { name: /Import/i });
    await user.click(importButton);

    expect(api.importResumeProfile).toHaveBeenCalledWith("run-demo-1");
    expect(await screen.findByText("Imported Candidate")).toBeInTheDocument();
    expect(screen.getByText("DevOps Engineer")).toBeInTheDocument();
  });
});
