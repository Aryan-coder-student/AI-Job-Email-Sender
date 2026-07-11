import { AlertTriangle, FileJson } from "lucide-react";

import { Button } from "@/shared/ui/button";
import { Card, CardContent } from "@/shared/ui/card";
import { StatusChip } from "@/shared/ui/status-chip";
import type { PipelineStepStatus } from "@/shared/types/pipeline";

export function PipelineStepper({
  steps,
  onOpenArtifact,
}: {
  steps: PipelineStepStatus[];
  onOpenArtifact?: (artifactType: string) => void;
}) {
  return (
    <div className="grid gap-3">
      {steps.map((step, index) => (
        <Card key={step.key}>
          <CardContent className="flex flex-col gap-3 p-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex min-w-0 gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted text-xs font-semibold">
                {index + 1}
              </div>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-semibold">{step.label}</h3>
                  <StatusChip status={step.status} />
                </div>
                <p className="mt-1 text-sm text-muted-foreground">
                  {step.error || step.summary || "Waiting for this step to run."}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {step.error ? <AlertTriangle className="h-4 w-4 text-destructive" /> : null}
              {step.artifact_type ? (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onOpenArtifact?.(step.artifact_type!)}
                >
                  <FileJson className="h-4 w-4" />
                  Artifact
                </Button>
              ) : null}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
