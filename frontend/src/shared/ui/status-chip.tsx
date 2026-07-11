import { CheckCircle2, Circle, Clock3, Loader2, XCircle } from "lucide-react";

import { Badge } from "@/shared/ui/badge";
import type { StepStatus } from "@/shared/types/pipeline";

const statusTone: Record<StepStatus, "neutral" | "green" | "amber" | "red" | "blue"> = {
  pending: "neutral",
  running: "blue",
  completed: "green",
  failed: "red",
  skipped: "amber",
};

const statusIcon = {
  pending: Circle,
  running: Loader2,
  completed: CheckCircle2,
  failed: XCircle,
  skipped: Clock3,
};

export function StatusChip({ status }: { status: StepStatus }) {
  const Icon = statusIcon[status];
  return (
    <Badge tone={statusTone[status]} className="gap-1 capitalize">
      <Icon className={status === "running" ? "h-3 w-3 animate-spin" : "h-3 w-3"} />
      {status}
    </Badge>
  );
}
