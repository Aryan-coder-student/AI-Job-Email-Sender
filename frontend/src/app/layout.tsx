import {
  BarChart3,
  BriefcaseBusiness,
  FileText,
  Github,
  LayoutDashboard,
  Mail,
  Menu,
  PlayCircle,
  Send,
  Settings,
  X,
} from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { RunPicker } from "@/features/runs/run-picker";
import { api } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { cn } from "@/shared/utils/cn";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/runs/new", label: "New Run", icon: PlayCircle },
  { to: "/candidate", label: "Candidate", icon: FileText },
  { to: "/companies", label: "Companies", icon: BriefcaseBusiness },
  { to: "/matches", label: "Matches", icon: BarChart3 },
  { to: "/drafts", label: "Drafts", icon: Mail },
  { to: "/queue", label: "Queue", icon: Send },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppLayout() {
  const [open, setOpen] = useState(false);
  const { data: status } = useQuery({
    queryKey: ["system-status"],
    queryFn: api.systemStatus,
  });

  return (
    <div className="min-h-screen bg-background">
      <div className="flex">
        <aside
          className={cn(
            "fixed inset-y-0 left-0 z-40 w-64 border-r border-border bg-card transition-transform lg:static lg:translate-x-0",
            open ? "translate-x-0" : "-translate-x-full",
          )}
        >
          <div className="flex h-14 items-center justify-between border-b border-border px-4">
            <div>
              <div className="text-sm font-semibold">Job Send Crawl</div>
              <div className="text-xs text-muted-foreground">Pipeline cockpit</div>
            </div>
            <Button
              aria-label="Close navigation"
              className="lg:hidden"
              size="icon"
              variant="ghost"
              onClick={() => setOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <nav className="grid gap-1 p-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setOpen(false)}
                  className={({ isActive }) =>
                    cn(
                      "flex h-9 items-center gap-2 rounded-md px-3 text-sm font-semibold text-muted-foreground hover:bg-muted hover:text-foreground",
                      isActive && "bg-muted text-foreground",
                    )
                  }
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
        </aside>

        <div className="min-w-0 flex-1">
          <header className="sticky top-0 z-30 flex min-h-14 flex-wrap items-center justify-between gap-2 border-b border-border bg-background/95 px-4 py-2 backdrop-blur">
            <div className="flex min-w-0 items-center gap-2">
              <Button
                aria-label="Open navigation"
                className="lg:hidden"
                size="icon"
                variant="outline"
                onClick={() => setOpen(true)}
              >
                <Menu className="h-4 w-4" />
              </Button>
              <Badge tone={status?.llm.configured ? "green" : "red"}>
                LLM {status?.llm.configured ? "ready" : "missing"}
              </Badge>
              <Badge tone={status?.dry_run_available ? "blue" : "neutral"}>dry run</Badge>
            </div>
            <div className="flex min-w-0 items-center gap-3">
              <RunPicker />
              <a
                className="hidden items-center gap-2 text-sm font-semibold text-muted-foreground hover:text-foreground sm:flex"
                href="https://github.com"
                rel="noreferrer"
                target="_blank"
              >
                <Github className="h-4 w-4" />
                Source
              </a>
            </div>
          </header>

          <main className="mx-auto w-full max-w-[1280px] p-4 lg:p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
