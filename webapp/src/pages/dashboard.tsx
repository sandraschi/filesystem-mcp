import { Activity, Bot, Cpu, FolderOpen, GitBranch, HardDrive, Server, Terminal, Wrench } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

const BACKEND_PORT = 10742;

interface StatusData {
  status: string;
  server: string;
  version: string;
  uptime_seconds: number;
  tool_count: number;
}

interface LlmProvider {
  name: string;
  detected: boolean;
}

export default function Dashboard() {
  const [status, setStatus] = useState<StatusData | null>(null);
  const [health, setHealth] = useState<boolean | null>(null);
  const [providers, setProviders] = useState<LlmProvider[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [statusRes, healthRes, llmRes] = await Promise.all([
        fetch(`http://127.0.0.1:${BACKEND_PORT}/api/status`, {
          signal: AbortSignal.timeout(5000),
        }),
        fetch(`http://127.0.0.1:${BACKEND_PORT}/api/health`, {
          signal: AbortSignal.timeout(5000),
        }),
        fetch(`http://127.0.0.1:${BACKEND_PORT}/api/llm/discover`, {
          signal: AbortSignal.timeout(5000),
        }),
      ]);
      if (statusRes.ok) setStatus((await statusRes.json()) as StatusData);
      setHealth(healthRes.ok);
      if (llmRes.ok) {
        const data = await llmRes.json();
        setProviders(data.providers ?? []);
      }
      setError(null);
    } catch (e) {
      setHealth(false);
      setError(e instanceof Error ? e.message : "Network error");
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 15000);
    return () => clearInterval(interval);
  }, [refresh]);

  const uptimeLabel = status?.uptime_seconds
    ? `${Math.floor(status.uptime_seconds / 60)}m ${Math.floor(status.uptime_seconds % 60)}s`
    : "—";
  const llmDetected = providers.some((p) => p.detected);

  return (
    <div data-testid="dashboard" className="space-y-8">
      <section className="rounded-2xl border border-border bg-gradient-to-br from-card to-card/60 p-8">
        <div className="flex items-center gap-3 text-green-500">
          <span
            data-testid="backend-dot"
            className={`h-2.5 w-2.5 rounded-full ${
              health === null ? "bg-slate-500 animate-pulse" : health ? "bg-green-500" : "bg-red-500"
            }`}
          />
          <span className="text-sm font-medium">
            {health === null ? "Connecting to backend..." : health ? "Backend connected" : "Backend offline"}
          </span>
        </div>
        <h1 className="mt-4 text-3xl font-bold tracking-tight">
          Filesystem MCP <span className="text-primary">Console</span>
        </h1>
        <p className="text-muted-foreground mt-2 max-w-2xl">
          Manage files, directories, Git repositories, and Docker containers through concurrency-safe MCP tools. Browse
          the file system, run searches, monitor system resources, and chat with your files using a local LLM.
        </p>
        <div className="flex flex-wrap gap-3 mt-6">
          <Link
            to="/files"
            className="inline-flex items-center gap-2 rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:bg-primary/90 transition-colors"
            data-testid="dashboard-cta-files"
          >
            <FolderOpen className="h-4 w-4" /> Browse Files
          </Link>
          <Link
            to="/docker"
            className="inline-flex items-center gap-2 rounded-md bg-accent px-4 py-2 text-sm font-medium hover:bg-accent/80 transition-colors"
          >
            <Server className="h-4 w-4" /> Docker
          </Link>
          <Link
            to="/chat"
            className="inline-flex items-center gap-2 rounded-md bg-accent px-4 py-2 text-sm font-medium hover:bg-accent/80 transition-colors"
          >
            <Bot className="h-4 w-4" /> Chat
          </Link>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div data-testid="kpi-server" className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center justify-between pb-2">
            <span className="text-sm font-medium text-muted-foreground">Server</span>
            <Activity className="h-4 w-4 text-green-500" />
          </div>
          <div className="text-2xl font-bold">{status?.server ?? "…"}</div>
          <div className="text-sm text-muted-foreground mt-1">v{status?.version ?? "—"}</div>
        </div>
        <div data-testid="kpi-tools" className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center justify-between pb-2">
            <span className="text-sm font-medium text-muted-foreground">Registered Tools</span>
            <Wrench className="h-4 w-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold">{status?.tool_count ?? "…"}</div>
          <div className="text-sm text-muted-foreground mt-1">MCP tool surface</div>
        </div>
        <div data-testid="kpi-uptime" className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center justify-between pb-2">
            <span className="text-sm font-medium text-muted-foreground">Uptime</span>
            <Cpu className="h-4 w-4 text-purple-500" />
          </div>
          <div className="text-2xl font-bold">{uptimeLabel}</div>
          <div className="text-sm text-muted-foreground mt-1">Since last start</div>
        </div>
        <div data-testid="kpi-llm" className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center justify-between pb-2">
            <span className="text-sm font-medium text-muted-foreground">Local LLM</span>
            <Bot className={`h-4 w-4 ${llmDetected ? "text-green-500" : "text-slate-500"}`} />
          </div>
          <div className="text-2xl font-bold">
            {providers.length === 0 ? "…" : llmDetected ? "Detected" : "Not found"}
          </div>
          <div className="text-sm text-muted-foreground mt-1">
            {providers
              .filter((p) => p.detected)
              .map((p) => p.name)
              .join(", ") || "Ollama / LM Studio"}
          </div>
        </div>
      </div>

      {!llmDetected && providers.length > 0 && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-300">
          No local LLM detected. Install or start{" "}
          <a href="https://ollama.com" target="_blank" rel="noreferrer" className="underline hover:text-amber-200">
            Ollama
          </a>{" "}
          or LM Studio to enable AI chat features in the Chat page.
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          Backend unreachable: {error}. Start it with <code className="font-mono text-red-300">webapp\start.ps1</code>{" "}
          and reload.
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <div className="col-span-4 rounded-xl border border-border bg-card p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <HardDrive className="h-4 w-4" /> Quick Actions
          </h3>
          <div className="grid gap-2 sm:grid-cols-2">
            <Link
              to="/files"
              className="rounded-md bg-accent px-4 py-2.5 text-sm font-medium hover:bg-accent/80 transition-colors"
            >
              Browse Files
            </Link>
            <Link
              to="/tools"
              className="rounded-md bg-accent px-4 py-2.5 text-sm font-medium hover:bg-accent/80 transition-colors"
            >
              View Tools
            </Link>
            <Link
              to="/git"
              className="rounded-md bg-accent px-4 py-2.5 text-sm font-medium hover:bg-accent/80 transition-colors"
            >
              Git Operations
            </Link>
            <Link
              to="/docker"
              className="rounded-md bg-accent px-4 py-2.5 text-sm font-medium hover:bg-accent/80 transition-colors"
            >
              Docker Console
            </Link>
          </div>
        </div>
        <div className="col-span-3 rounded-xl border border-border bg-card p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <GitBranch className="h-4 w-4" /> Capabilities
          </h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-center gap-2">
              <Terminal className="h-3.5 w-3.5 text-primary" /> 24 MCP tools, portmanteau grouped
            </li>
            <li className="flex items-center gap-2">
              <Server className="h-3.5 w-3.5 text-primary" /> Dual transport: stdio + HTTP
            </li>
            <li className="flex items-center gap-2">
              <HardDrive className="h-3.5 w-3.5 text-primary" /> Concurrency-safe atomic writes
            </li>
            <li className="flex items-center gap-2">
              <Bot className="h-3.5 w-3.5 text-primary" /> Agentic workflows via ctx.sample()
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
