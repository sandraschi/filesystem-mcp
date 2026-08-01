import { Cpu, Database, FileCode, Globe, Grid } from "lucide-react";
import { Link } from "react-router-dom";
import { cn } from "@/shared/utils";

const apps = [
  {
    title: "Code Review",
    description: "Review code for quality, security, and performance issues.",
    icon: FileCode,
    href: "/chat?context=code-review",
    color: "text-blue-500",
    bg: "bg-blue-500/10",
  },
  {
    title: "Log Analyzer",
    description: "Parse and analyze system logs for anomalies.",
    icon: Database,
    href: "/chat?context=log-analysis",
    color: "text-amber-500",
    bg: "bg-amber-500/10",
  },
  {
    title: "System Doctor",
    description: "Diagnose system health and performance issues.",
    icon: Cpu,
    href: "/chat?context=system-health",
    color: "text-red-500",
    bg: "bg-red-500/10",
  },
  {
    title: "Large File Hunt",
    description: "Find large files and duplicate data on disk.",
    icon: Globe,
    href: "/chat?context=large-files",
    color: "text-green-500",
    bg: "bg-green-500/10",
  },
  {
    title: "Disk Space Audit",
    description: "Analyze disk usage and find cleanup targets.",
    icon: Grid,
    href: "/chat?context=disk-audit",
    color: "text-purple-500",
    bg: "bg-purple-500/10",
  },
];

export default function Apps() {
  return (
    <div data-testid="apps-page" className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Apps</h1>
        <p className="text-muted-foreground mt-2">
          Pre-filled chat workflows that drive the MCP tool surface with your local LLM.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {apps.map((app) => (
          <Link
            key={app.title}
            to={app.href}
            data-testid={`app-card-${app.title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
            className="group relative overflow-hidden rounded-xl border border-border bg-card p-6 transition-all hover:shadow-md hover:border-primary/50"
          >
            <div className="flex items-center gap-4">
              <div className={cn("p-3 rounded-lg transition-colors", app.bg)}>
                <app.icon className={cn("w-6 h-6", app.color)} />
              </div>
              <div>
                <h3 className="font-semibold leading-none tracking-tight">{app.title}</h3>
              </div>
            </div>
            <p className="mt-4 text-sm text-muted-foreground line-clamp-2">{app.description}</p>
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-primary/5 opacity-0 transition-opacity group-hover:opacity-100" />
          </Link>
        ))}
      </div>
    </div>
  );
}
