import { ArrowUpRight, GitBranch } from "lucide-react";

export default function GitOps() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Git Operations — moved</h1>
        <p className="text-muted-foreground mt-2">
          Git lives in <code className="font-mono">git-github-mcp</code> now (
          <code className="font-mono">gitops:git_core</code> / <code className="font-mono">github_ops</code>). This page
          no longer calls the removed <code className="font-mono">repo_ops</code> tool.
        </p>
      </div>

      <div className="rounded-xl border border-border bg-card p-6 space-y-4">
        <div className="flex items-center gap-2 text-sm">
          <GitBranch className="w-4 h-4 text-orange-500" />
          <span>Use the git-github-mcp webapp / MCP tools for status, log, diff, commit, push, pull, clone.</span>
        </div>
        <a
          href="https://github.com/sandraschi/git-github-mcp"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Open git-github-mcp <ArrowUpRight className="w-4 h-4" />
        </a>
      </div>
    </div>
  );
}
