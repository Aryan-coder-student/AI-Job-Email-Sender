import { NewRunWizard } from "@/features/runs/new-run-wizard";

export function NewRunPage() {
  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold">New run</h1>
        <p className="text-sm text-muted-foreground">
          Configure resume, company data, matching, and mail behavior.
        </p>
      </div>
      <NewRunWizard />
    </div>
  );
}
