import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import type { ArtifactType } from "@/shared/types/pipeline";

export function ArtifactPanel({
  runId,
  artifactType,
}: {
  runId: string;
  artifactType: ArtifactType;
}) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["artifact", runId, artifactType],
    queryFn: () => api.artifact<unknown>(runId, artifactType),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>{artifactType} artifact</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading artifact...</p>
        ) : error ? (
          <p className="text-sm text-destructive">Artifact is not available.</p>
        ) : (
          <pre className="max-h-96 overflow-auto rounded-md bg-muted p-3 text-xs">
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </CardContent>
    </Card>
  );
}
