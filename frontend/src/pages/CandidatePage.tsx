import { useQuery } from "@tanstack/react-query";

import { useActiveRun } from "@/features/runs/hooks";
import { api } from "@/shared/api/client";
import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import type { ParsedResume } from "@/shared/types/pipeline";

export function CandidatePage() {
  const { runId } = useActiveRun();
  const { data: resume, isLoading } = useQuery({
    queryKey: ["artifact", runId, "resume"],
    queryFn: () => api.artifact<ParsedResume>(runId, "resume"),
  });

  if (isLoading || !resume) {
    return <p className="text-sm text-muted-foreground">Loading candidate profile...</p>;
  }

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold">{resume.candidate_name ?? "Candidate"}</h1>
        <p className="text-sm text-muted-foreground">{resume.filename}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4">
          <p className="text-sm">{resume.summary || "No summary extracted."}</p>
          <div className="flex flex-wrap gap-2">
            {resume.skills.map((skill) => (
              <Badge key={skill}>{skill}</Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Experience</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            {resume.experience.map((item, index) => (
              <div key={`${item.company_name}-${index}`} className="rounded-md border border-border p-3">
                <div className="font-semibold">{item.company_name ?? "Experience"}</div>
                <div className="text-xs text-muted-foreground">{item.date}</div>
                <p className="mt-2 text-sm">{item.description}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Projects</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            {resume.projects.map((project, index) => (
              <div key={`${project.project_name}-${index}`} className="rounded-md border border-border p-3">
                <div className="font-semibold">{project.project_name ?? "Project"}</div>
                {project.link ? (
                  <a className="text-xs text-primary" href={project.link} target="_blank" rel="noreferrer">
                    {project.link}
                  </a>
                ) : null}
                <p className="mt-2 text-sm">{project.description}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Raw text</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="max-h-80 overflow-auto rounded-md bg-muted p-3 text-xs">
            {resume.raw_text}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
