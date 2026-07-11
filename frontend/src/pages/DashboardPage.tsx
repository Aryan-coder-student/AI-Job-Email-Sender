import { useQuery } from "@tanstack/react-query";
import { ArrowRight, PlayCircle } from "lucide-react";
import { Link } from "react-router-dom";

import { api } from "@/shared/api/client";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { DataTable, Td, Th } from "@/shared/ui/data-table";
import { StatusChip } from "@/shared/ui/status-chip";

export function DashboardPage() {
  const { data: runs = [] } = useQuery({ queryKey: ["runs"], queryFn: api.listRuns });
  const { data: status } = useQuery({ queryKey: ["system-status"], queryFn: api.systemStatus });
  const activeRun = runs[0];

  return (
    <div className="grid gap-4">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-semibold">Pipeline cockpit</h1>
          <p className="text-sm text-muted-foreground">
            Upload inputs, run the pipeline, review matches, and send with control.
          </p>
        </div>
        <Button asChild>
          <Link to="/runs/new">
            <PlayCircle className="h-4 w-4" />
            New run
          </Link>
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Current run</CardTitle>
          </CardHeader>
          <CardContent>
            {activeRun ? (
              <div className="grid gap-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm">{activeRun.run_id}</span>
                  <Badge tone={activeRun.status === "completed" ? "green" : "blue"}>
                    {activeRun.status}
                  </Badge>
                </div>
                <Button asChild variant="outline">
                  <Link to={`/runs/${activeRun.run_id}`}>
                    Open run
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No runs yet.</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>LLM readiness</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {Object.entries(status?.llm.providers ?? {}).map(([name, provider]) => (
              <Badge key={name} tone={provider.configured ? "green" : "red"}>
                {name}: {provider.configured ? "ready" : "missing"}
              </Badge>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Services</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {Object.entries(status?.services ?? {}).map(([name, service]) => (
              <Badge key={name} tone={service.configured ? "green" : "amber"}>
                {name}
              </Badge>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent runs</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable>
            <thead>
              <tr>
                <Th>Run</Th>
                <Th>Status</Th>
                <Th>Target</Th>
                <Th>Steps</Th>
                <Th></Th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.run_id}>
                  <Td className="font-mono">{run.run_id}</Td>
                  <Td>
                    <Badge tone={run.status === "completed" ? "green" : "blue"}>{run.status}</Badge>
                  </Td>
                  <Td>{String(run.config.target_company ?? "-")}</Td>
                  <Td className="flex flex-wrap gap-1">
                    {run.steps.slice(0, 3).map((step) => (
                      <StatusChip key={step.key} status={step.status} />
                    ))}
                  </Td>
                  <Td className="text-right">
                    <Button asChild size="sm" variant="outline">
                      <Link to={`/runs/${run.run_id}`}>Open</Link>
                    </Button>
                  </Td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        </CardContent>
      </Card>
    </div>
  );
}
