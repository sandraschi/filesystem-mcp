import { Link } from "react-router-dom";
import { cn } from "@/shared/utils";
import { FileText, Search, Box, Code, Activity, Shield } from "lucide-react";

const tools = [
    {
        title: "File Operations",
        description: "Read, write, move, and edit files with safety checks.",
        icon: FileText,
        href: "/files",
        color: "text-blue-500",
        bg: "bg-blue-500/10",
    },
    {
        title: "Search & Analysis",
        description: "Grep-based search, pattern matching, and content analysis.",
        icon: Search,
        href: "#",
        color: "text-green-500",
        bg: "bg-green-500/10",
    },
    {
        title: "Git Operations",
        description: "Branch management, commits, history, and diffs.",
        icon: Code,
        href: "/git",
        color: "text-orange-500",
        bg: "bg-orange-500/10",
    },
    {
        title: "Docker Ops",
        description: "Container lifecycle, image management, and networks.",
        icon: Box,
        href: "/docker",
        color: "text-sky-500",
        bg: "bg-sky-500/10",
    },
    {
        title: "System Monitor",
        description: "Real-time CPU, memory, and disk usage metrics.",
        icon: Activity,
        href: "/logs",
        color: "text-purple-500",
        bg: "bg-purple-500/10",
    },
    {
        title: "Host Context",
        description: "Environment variables, user info, and system details.",
        icon: Shield,
        href: "#",
        color: "text-red-500",
        bg: "bg-red-500/10",
    },
];

export default function Tools() {
    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Tools</h1>
                <p className="text-muted-foreground mt-2">Access powerful filesystem and system operations.</p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {tools.map((tool) => (
                    <Link
                        key={tool.title}
                        to={tool.href}
                        className="group relative overflow-hidden rounded-xl border border-border bg-card p-6 transition-all hover:shadow-md hover:border-primary/50"
                    >
                        <div className="flex items-center gap-4">
                            <div className={cn("p-3 rounded-lg transition-colors", tool.bg)}>
                                <tool.icon className={cn("w-6 h-6", tool.color)} />
                            </div>
                            <div>
                                <h3 className="font-semibold leading-none tracking-tight">{tool.title}</h3>
                            </div>
                        </div>
                        <p className="mt-4 text-sm text-muted-foreground line-clamp-2">
                            {tool.description}
                        </p>
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-primary/5 opacity-0 transition-opacity group-hover:opacity-100" />
                    </Link>
                ))}
            </div>
        </div>
    );
}
