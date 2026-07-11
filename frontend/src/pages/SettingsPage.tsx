import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/api/client";
import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { DataTable, Td, Th } from "@/shared/ui/data-table";

export function SettingsPage() {
  const { data: status } = useQuery({ queryKey: ["system-status"], queryFn: api.systemStatus });

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">Masked readiness only. Secret values stay server-side.</p>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>LLM providers</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable>
              <thead>
                <tr>
                  <Th>Provider</Th>
                  <Th>Status</Th>
                  <Th>Model</Th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(status?.llm.providers ?? {}).map(([name, provider]) => (
                  <tr key={name}>
                    <Td>{name}</Td>
                    <Td>
                      <Badge tone={provider.configured ? "green" : "red"}>
                        {provider.configured ? "configured" : "missing"}
                      </Badge>
                    </Td>
                    <Td>{provider.model ?? "-"}</Td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Services</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable>
              <thead>
                <tr>
                  <Th>Service</Th>
                  <Th>Status</Th>
                  <Th>Endpoint</Th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(status?.services ?? {}).map(([name, service]) => (
                  <tr key={name}>
                    <Td>{name}</Td>
                    <Td>
                      <Badge tone={service.configured ? "green" : "amber"}>
                        {service.configured ? "configured" : "missing"}
                      </Badge>
                    </Td>
                    <Td className="font-mono text-xs">{service.url ?? service.provider ?? "-"}</Td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
