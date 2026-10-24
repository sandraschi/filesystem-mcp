import { Activity, Box, FileText, Search, Shield } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { API_BASE } from "@/shared/api-base";
import { cn } from "@/shared/utils";

const tools = [
  {
    title: "File Operations",
    description: "Read, write, hash, append, compress, and edit files with safety checks.",
    icon: FileText,
    href: "/files",
    color: "text-blue-500",
    bg: "bg-blue-500/10",
  },
  {
    title: "Search & Analysis",
    description: "Grep, todos, symbols, project analysis, lint, and config validation.",
    icon: Search,
    href: "/files",
    color: "text-green-500",
    bg: "bg-green-500/10",
  },
  {
    title: "Docker Ops (deprecated)",
    description: "Kept for local convenience — docker-mcp owns this surface.",
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
    href: "/settings",
    color: "text-red-500",
    bg: "bg-red-500/10",
  },
];

export default function Tools() {
  const [toolNames, setToolNames] = useState<string[]>([]);
  const [toolCount, setToolCount] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/capabilities`, { signal: AbortSignal.timeout(5000) });
        if (!res.ok) return;
        const data = await res.json();
        const names: string[] = data?.capabilities?.tools ?? [];
        if (!cancelled && Array.isArray(names)) {
          setToolNames(names);
          setToolCount(names.length);
        }
      } catch {
        /* backend offline — static cards still render */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div data-testid="tools-page" className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Tools</h1>
        <p className="text-muted-foreground mt-2">
          Access powerful filesystem and system operations.{" "}
          <span className="text-primary/80">
            {toolCount === null
              ? "MCP tools are exposed over MCP — connect via Cursor, Claude Desktop, or any MCP client."
              : `${toolCount} tools live on this backend — connect via Cursor, Claude Desktop, or any MCP client.`}{" "}
            Git lives in git-github-mcp; Docker ownership is docker-mcp.
          </span>
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {tools.map((tool) => (
          <Link
            key={tool.title}
            to={tool.href}
            data-testid={`tool-card-${tool.title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
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
            <p className="mt-4 text-sm text-muted-foreground line-clamp-2">{tool.description}</p>
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-primary/5 opacity-0 transition-opacity group-hover:opacity-100" />
          </Link>
        ))}
      </div>

      {toolNames.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-6">
          <h3 className="font-semibold mb-3">Live tool surface ({toolNames.length})</h3>
          <div className="flex flex-wrap gap-2">
            {toolNames.map((name) => (
              <code key={name} className="rounded bg-accent px-2 py-1 font-mono text-xs">
                {name}
              </code>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
