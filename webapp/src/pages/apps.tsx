import { Grid, FileCode, Database, Cpu, Globe } from "lucide-react";
import { Link } from "react-router-dom";
import { cn } from "@/shared/utils";

const apps = [
    {
        title: "Code Review",
        description: "Automated code analysis and improvement suggestions.",
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
        title: "Web Scraper",
        description: "Extract data from websites (Mock).",
        icon: Globe,
        href: "/chat?context=web-scraper",
        color: "text-green-500",
        bg: "bg-green-500/10",
    },
    {
        title: "App Factory",
        description: "Scaffold new applications from templates.",
        icon: Grid,
        href: "/chat?context=app-factory",
        color: "text-purple-500",
        bg: "bg-purple-500/10",
    },
];

export default function Apps() {
    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Apps</h1>
                <p className="text-muted-foreground mt-2">Specialized workflows and AI applications.</p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {apps.map((app) => (
                    <Link
                        key={app.title}
                        to={app.href}
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
                        <p className="mt-4 text-sm text-muted-foreground line-clamp-2">
                            {app.description}
                        </p>
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-primary/5 opacity-0 transition-opacity group-hover:opacity-100" />
                    </Link>
                ))}
            </div>
        </div>
    );
}
