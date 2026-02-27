import { useState } from "react";
import { GitBranch, GitCommit, Loader2 } from "lucide-react";
import { useMcp } from "@/shared/mcp-provider";

export default function GitOps() {
    const { client, isConnected } = useMcp();
    const [repoPath, setRepoPath] = useState("D:\\Dev\\repos\\filesystem-mcp");
    const [status, setStatus] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const checkStatus = async () => {
        if (!isConnected) return;
        setLoading(true);
        setError(null);
        try {
            // repo_ops is the tool for status
            const result = await client.callTool("repo_ops", {
                operation: "get_repo_status",
                repo_path: repoPath
            });
            setStatus(result);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Git Operations</h1>
                <p className="text-muted-foreground mt-2">Manage repositories and view status.</p>
            </div>

            <div className="rounded-xl border border-border bg-card p-6 space-y-6">
                <div className="flex gap-4">
                    <input
                        value={repoPath}
                        onChange={(e) => setRepoPath(e.target.value)}
                        className="flex-1 bg-background border border-input rounded-md px-3 py-2 text-sm"
                        placeholder="Repository Path"
                    />
                    <button
                        onClick={checkStatus}
                        disabled={loading || !isConnected}
                        className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2"
                    >
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitBranch className="w-4 h-4" />}
                        Check Status
                    </button>
                </div>

                {error && (
                    <div className="p-4 bg-red-500/10 text-red-500 rounded-lg text-sm">
                        Error: {error}
                    </div>
                )}

                {status && (
                    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2">
                        <div className="grid grid-cols-3 gap-4">
                            <div className="p-4 bg-background border border-border rounded-lg">
                                <div className="text-xs text-muted-foreground uppercase tracking-wide">Current Branch</div>
                                <div className="text-xl font-bold mt-1 flex items-center gap-2">
                                    <GitBranch className="w-4 h-4 text-orange-500" />
                                    {status.branch || "main"}
                                </div>
                            </div>
                            <div className="p-4 bg-background border border-border rounded-lg">
                                <div className="text-xs text-muted-foreground uppercase tracking-wide">Changed Files</div>
                                <div className="text-xl font-bold mt-1 flex items-center gap-2">
                                    <GitCommit className="w-4 h-4 text-blue-500" />
                                    {/* Mock count if not in standard result structure */}
                                    {(status.changed_files?.length) || 0}
                                </div>
                            </div>
                        </div>

                        <div className="p-4 bg-background border border-border rounded-lg font-mono text-sm whitespace-pre overflow-auto">
                            {JSON.stringify(status, null, 2)}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
