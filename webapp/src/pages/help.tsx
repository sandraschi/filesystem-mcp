import { FileText, Terminal, Github, Server, ExternalLink } from "lucide-react";

export default function Help() {
    return (
        <div className="space-y-8 max-w-4xl mx-auto">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Documentation</h1>
                <p className="text-muted-foreground mt-2">Guides and references for filesystem-mcp.</p>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <div className="rounded-xl border border-border bg-card p-6 space-y-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-500/10 rounded-lg text-blue-500">
                            <FileText className="w-5 h-5" />
                        </div>
                        <h2 className="text-xl font-semibold">File Operations</h2>
                    </div>
                    <p className="text-sm text-muted-foreground">
                        Learn how to safely read, write, move, and edit files. Calls are sandboxed and backed up by default.
                    </p>
                    <ul className="list-disc list-inside text-sm space-y-1 text-muted-foreground/80 pl-2">
                        <li>read_file / write_file</li>
                        <li>edit_file (patch check)</li>
                        <li>move_file / copy_file</li>
                    </ul>
                </div>

                <div className="rounded-xl border border-border bg-card p-6 space-y-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-orange-500/10 rounded-lg text-orange-500">
                            <Github className="w-5 h-5" />
                        </div>
                        <h2 className="text-xl font-semibold">Git Integration</h2>
                    </div>
                    <p className="text-sm text-muted-foreground">
                        Manage repositories, branches, and commits directly from the interface.
                    </p>
                    <ul className="list-disc list-inside text-sm space-y-1 text-muted-foreground/80 pl-2">
                        <li>clone_repo / init_repo</li>
                        <li>commit_changes</li>
                        <li>push_changes / pull_changes</li>
                    </ul>
                </div>

                <div className="rounded-xl border border-border bg-card p-6 space-y-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-sky-500/10 rounded-lg text-sky-500">
                            <Server className="w-5 h-5" />
                        </div>
                        <h2 className="text-xl font-semibold">Docker Management</h2>
                    </div>
                    <p className="text-sm text-muted-foreground">
                        Control containers, images, and volumes. View logs and stats in real-time.
                    </p>
                    <ul className="list-disc list-inside text-sm space-y-1 text-muted-foreground/80 pl-2">
                        <li>list_containers</li>
                        <li>start_container / stop_container</li>
                        <li>get_container_logs</li>
                    </ul>
                </div>

                <div className="rounded-xl border border-border bg-card p-6 space-y-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-purple-500/10 rounded-lg text-purple-500">
                            <Terminal className="w-5 h-5" />
                        </div>
                        <h2 className="text-xl font-semibold">CLI Reference</h2>
                    </div>
                    <p className="text-sm text-muted-foreground">
                        Complete reference for all MCP tools and their arguments.
                    </p>
                    <button className="flex items-center gap-2 text-sm text-primary hover:underline">
                        View CLI Docs <ExternalLink className="w-3 h-3" />
                    </button>
                </div>
            </div>

            <div className="rounded-xl border border-border bg-card/50 p-6">
                <h3 className="font-semibold mb-2">Need more help?</h3>
                <p className="text-sm text-muted-foreground">
                    Check the <a href="#" className="text-primary hover:underline">Support Channel</a> or open an issue on GitHub.
                </p>
            </div>
        </div>
    );
}
