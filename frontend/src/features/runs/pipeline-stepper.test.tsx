import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PipelineStepper } from "@/features/runs/pipeline-stepper";

describe("PipelineStepper", () => {
  it("renders step statuses and artifact actions", () => {
    render(
      <PipelineStepper
        steps={[
          {
            key: "parse_resume",
            label: "Parse Resume",
            status: "completed",
            artifact_type: "resume",
            summary: "Parsed resume",
          },
          {
            key: "rank_projects",
            label: "Rank Projects",
            status: "pending",
          },
        ]}
      />,
    );

    expect(screen.getByText("Parse Resume")).toBeInTheDocument();
    expect(screen.getByText("completed")).toBeInTheDocument();
    expect(screen.getByText("Rank Projects")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /artifact/i })).toBeInTheDocument();
  });
});
