import { Sparkles, Wrench } from "lucide-react";
import { useEffect, useState } from "react";
import { API_BASE } from "@/shared/api-base";
import { type McpTool, mcpClient } from "@/shared/mcp-client";

interface PromptInfo {
  name: string;
  description?: string;
}

export default function Skills() {
  const [tools, setTools] = useState<McpTool[]>([]);
  const [prompts, setPrompts] = useState<PromptInfo[]>([]);
  const [sessionSkills, setSessionSkills] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await mcpClient.connect();
        const [livePrompts, skillsRes] = await Promise.all([
          mcpClient.listPrompts(),
          fetch(`${API_BASE}/api/skills`, { signal: AbortSignal.timeout(8000) }),
        ]);
        if (cancelled) return;
        setTools(mcpClient.getTools());
        setPrompts(livePrompts);
        if (skillsRes.ok) {
          const data = await skillsRes.json();
          setSessionSkills((data.skills ?? []).map((s: unknown) => (typeof s === "string" ? s : JSON.stringify(s))));
        }
        setError(null);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Network error");
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div data-testid="skills-page" className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Skills</h1>
        <p className="text-muted-foreground mt-2">
          Prompt templates and the live MCP tool catalog, straight from the running server.
        </p>
      </div>

      {error && (
        <div
          data-testid="skills-error"
          className="p-4 rounded-lg bg-red-500/10 text-red-500 text-sm border border-red-500/20"
        >
          Backend unreachable: {error}. Start it with <code className="font-mono">.\start.ps1 -BackendOnly</code>
        </div>
      )}

      {isLoading && !error && (
        <div data-testid="skills-loading" className="p-8 text-center text-muted-foreground text-sm">
          Loading skills...
        </div>
      )}

      <section>
        <h2 className="text-xl font-semibold mb-3">Prompt templates ({prompts.length})</h2>
        {prompts.length === 0 && !isLoading ? (
          <p data-testid="skills-prompts-empty" className="text-sm text-muted-foreground">
            No prompt templates registered on this server.
          </p>
        ) : (
          <div data-testid="skills-prompts" className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {prompts.map((p) => (
              <div
                key={p.name}
                data-testid={`skill-prompt-${p.name}`}
                className="rounded-xl border border-border bg-card p-5"
              >
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-primary" />
                  <h3 className="font-semibold font-mono text-sm">{p.name}</h3>
                </div>
                {p.description && <p className="mt-2 text-sm text-muted-foreground">{p.description}</p>}
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-3">Tool catalog ({tools.length})</h2>
        <div data-testid="skills-tools" className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {tools.map((t) => (
            <div
              key={t.name}
              data-testid={`skill-tool-${t.name}`}
              className="rounded-xl border border-border bg-card p-5"
            >
              <div className="flex items-center gap-2">
                <Wrench className="w-4 h-4 text-primary" />
                <h3 className="font-semibold font-mono text-sm">{t.name}</h3>
              </div>
              {t.description && <p className="mt-2 text-sm text-muted-foreground line-clamp-3">{t.description}</p>}
            </div>
          ))}
        </div>
      </section>

      {sessionSkills.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-3">Session skills ({sessionSkills.length})</h2>
          <ul data-testid="skills-session" className="list-disc list-inside text-sm text-muted-foreground space-y-1">
            {sessionSkills.map((s) => (
              <li key={s} className="font-mono">
                {s}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
