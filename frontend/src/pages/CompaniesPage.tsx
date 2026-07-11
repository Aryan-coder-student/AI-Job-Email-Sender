import { useQuery } from "@tanstack/react-query";
import { ExternalLink } from "lucide-react";
import { useMemo, useState } from "react";

import { useActiveRun } from "@/features/runs/hooks";
import { api } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { DataTable, Td, Th } from "@/shared/ui/data-table";
import { Input } from "@/shared/ui/form";

export function CompaniesPage() {
  const [query, setQuery] = useState("");
  const { runId } = useActiveRun();
  const { data: companies = [], isLoading } = useQuery({
    queryKey: ["companies", runId],
    queryFn: () => api.companies(runId),
  });
  const filteredCompanies = useMemo(
    () =>
      companies.filter((company) =>
        JSON.stringify(company).toLowerCase().includes(query.toLowerCase()),
      ),
    [companies, query],
  );

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Companies</h1>
        <p className="text-sm text-muted-foreground">Review company, role, and contact data.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Company records</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3">
          <Input placeholder="Search companies..." value={query} onChange={(event) => setQuery(event.target.value)} />
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading companies...</p>
          ) : (
            <DataTable>
              <thead>
                <tr>
                  <Th>Company</Th>
                  <Th>Role</Th>
                  <Th>Contact</Th>
                  <Th>Source</Th>
                  <Th></Th>
                </tr>
              </thead>
              <tbody>
                {filteredCompanies.map((company, index) => (
                  <tr key={`${company.company_name}-${index}`}>
                    <Td>
                      <div className="font-semibold">{company.company_name ?? "Unknown"}</div>
                      <div className="max-w-md truncate text-xs text-muted-foreground">
                        {company.company_description}
                      </div>
                    </Td>
                    <Td>{company.role ?? "-"}</Td>
                    <Td>
                      <div>{company.hr_email ?? "-"}</div>
                      <div className="text-xs text-muted-foreground">{company.contact_name}</div>
                    </Td>
                    <Td>
                      {company.source_sheet ?? "-"} {company.source_row ? `#${company.source_row}` : ""}
                    </Td>
                    <Td className="text-right">
                      {company.job_url || company.company_url ? (
                        <Button asChild size="sm" variant="outline">
                          <a href={String(company.job_url || company.company_url)} target="_blank" rel="noreferrer">
                            <ExternalLink className="h-4 w-4" />
                            Open
                          </a>
                        </Button>
                      ) : null}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
