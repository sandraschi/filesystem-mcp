import { CheckCircle2, Inbox as InboxIcon, RefreshCw, Search, XCircle } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { API_BASE } from "@/shared/api-base";
import { cn } from "@/shared/utils";

interface ActivityItem {
  ts: string;
  operation: string;
  success: boolean;
}

export default function Inbox() {
  const [items, setItems] = useState<ActivityItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | "ok" | "failed">("all");

  const refresh = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/api/activity?limit=100`, {
        signal: AbortSignal.timeout(8000),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setItems(data.items ?? []);
      setTotal(data.total ?? 0);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Network error");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 10000);
    return () => clearInterval(interval);
  }, [refresh]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items.filter((it) => {
      if (filter === "ok" && !it.success) return false;
      if (filter === "failed" && it.success) return false;
      if (q && !it.operation.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [items, query, filter]);

  return (
    <div data-testid="inbox-page" className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Inbox</h1>
        <p className="text-muted-foreground mt-2">
          Live receipts for every tool action on this server (newest first, in-memory ring of 100).
        </p>
      </div>

      <div data-testid="inbox-controls" className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-52">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            data-testid="inbox-search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by operation..."
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-border bg-card text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>
        <div data-testid="inbox-filter" className="flex rounded-lg border border-border overflow-hidden">
          {(["all", "ok", "failed"] as const).map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f)}
              className={cn(
                "px-4 py-2 text-sm capitalize transition-colors",
                filter === f ? "bg-primary text-primary-foreground" : "hover:bg-accent",
              )}
            >
              {f === "all" ? `All (${total})` : f}
            </button>
          ))}
        </div>
        <button
          type="button"
          data-testid="inbox-refresh"
          onClick={refresh}
          className="p-2 rounded-lg border border-border hover:bg-accent"
          title="Refresh now"
        >
          <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
        </button>
      </div>

      {error && (
        <div
          data-testid="inbox-error"
          className="p-4 rounded-lg bg-red-500/10 text-red-500 text-sm border border-red-500/20"
        >
          Backend unreachable: {error}. Start it with <code className="font-mono">.\start.ps1 -BackendOnly</code>
        </div>
      )}

      {isLoading && items.length === 0 && !error && (
        <div data-testid="inbox-loading" className="p-8 text-center text-muted-foreground text-sm">
          Loading activity...
        </div>
      )}

      {!isLoading && visible.length === 0 && !error && (
        <div data-testid="inbox-empty" className="p-8 text-center rounded-xl border border-dashed border-border">
          <InboxIcon className="w-8 h-8 mx-auto text-muted-foreground" />
          <p className="mt-3 text-sm text-muted-foreground">
            {items.length === 0
              ? "No tool actions recorded yet in this server process. Run any tool (or refresh a page) and receipts appear here."
              : "No receipts match this filter."}
          </p>
        </div>
      )}

      <div data-testid="inbox-list" className="space-y-2">
        {visible.map((it) => (
          <div
            key={`${it.ts}-${it.operation}`}
            data-testid={`inbox-item-${it.success ? "ok" : "failed"}`}
            className="flex items-center gap-3 p-3 rounded-lg border border-border bg-card"
          >
            {it.success ? (
              <CheckCircle2 className="w-4 h-4 shrink-0 text-green-500" />
            ) : (
              <XCircle className="w-4 h-4 shrink-0 text-red-500" />
            )}
            <span className="font-mono text-sm flex-1 truncate">{it.operation}</span>
            <span className="text-xs text-muted-foreground font-mono">{new Date(it.ts).toLocaleTimeString()}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
