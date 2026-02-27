import { useState, useEffect } from "react";
import { Play, Square, RefreshCw } from "lucide-react";
import { useMcp } from "@/shared/mcp-provider";

export default function DockerOps() {
    const { client, isConnected } = useMcp();
    const [containers, setContainers] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchContainers = async () => {
        if (!isConnected) return;
        setLoading(true);
        setError(null);
        try {
            const result = await client.callTool("container_ops", {
                operation: "list_containers",
                all: true
            });

            const data = result as any;
            let items: any[] = [];

            if (Array.isArray(data)) items = data;
            else if (data.containers) items = data.containers;
            else if (data.result && Array.isArray(data.result)) items = data.result;

            setContainers(items);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (isConnected) fetchContainers();
    }, [isConnected]);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold tracking-tight">Docker Operations</h1>
                <button
                    onClick={fetchContainers}
                    className="p-2 hover:bg-accent rounded-md"
                >
                    <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
                </button>
            </div>

            <div className="rounded-xl border border-border bg-card overflow-hidden">
                {error && (
                    <div className="p-4 bg-red-500/10 text-red-500 text-sm border-b border-border">
                        {error}
                    </div>
                )}

                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-muted/50 text-muted-foreground uppercase text-xs">
                            <tr>
                                <th className="px-6 py-3">Container ID</th>
                                <th className="px-6 py-3">Image</th>
                                <th className="px-6 py-3">Status</th>
                                <th className="px-6 py-3">Names</th>
                                <th className="px-6 py-3 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {containers.length === 0 && !loading && (
                                <tr>
                                    <td colSpan={5} className="px-6 py-8 text-center text-muted-foreground">
                                        No containers found
                                    </td>
                                </tr>
                            )}
                            {containers.map((c) => (
                                <tr key={c.Id || c.id} className="hover:bg-accent/50 transition-colors">
                                    <td className="px-6 py-4 font-mono text-xs">{c.Id?.substring(0, 12)}</td>
                                    <td className="px-6 py-4 text-blue-400">{c.Image}</td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${c.State === 'running' ? 'bg-green-500/10 text-green-500' : 'bg-gray-500/10 text-gray-400'
                                            }`}>
                                            {c.State}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">{c.Names?.[0] || c.Name}</td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="flex justify-end gap-2">
                                            <button className="p-1 hover:bg-green-500/10 text-green-500 rounded">
                                                <Play className="w-4 h-4" />
                                            </button>
                                            <button className="p-1 hover:bg-red-500/10 text-red-500 rounded">
                                                <Square className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
