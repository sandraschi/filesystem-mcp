import { useState, useEffect } from "react";
import { Folder, File, ArrowLeft, RefreshCw, FileCode, FileImage } from "lucide-react";
import { useMcp } from "@/shared/mcp-provider";
import { cn } from "@/shared/utils";

type FileEntry = {
    name: string;
    type: "file" | "directory";
    size?: number;
    children?: number;
    path: string; // Relative or full path
};

export default function FileBrowser() {
    const { client, isConnected } = useMcp();
    // State
    const [currentPath, setCurrentPath] = useState<string>("C:\\"); // Default start
    const [entries, setEntries] = useState<FileEntry[]>([]);
    const [history, setHistory] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedFile, setSelectedFile] = useState<{ name: string, content: string } | null>(null);

    const fetchDirectory = async (path: string) => {
        if (!isConnected) return;
        setIsLoading(true);
        setError(null);
        try {
            const result = await client.callTool("dir_ops", {
                operation: "list_directory",
                path
            });

            const data = result as any;

            let items: any[] = [];
            if (Array.isArray(data)) {
                items = data;
            } else if (data.items && Array.isArray(data.items)) {
                items = data.items;
            } else if (data.files && Array.isArray(data.files)) {
                items = [...(data.directories || []).map((d: any) => ({ ...d, type: 'directory' })),
                ...(data.files || []).map((f: any) => ({ ...f, type: 'file' }))];
            } else if (typeof data === 'string') {
                setError("Received string response: " + data);
                return;
            }

            const parsedEntries: FileEntry[] = items.map((item: any) => ({
                name: item.name || item.path?.split(/[\\/]/).pop() || "Unknown",
                type: item.type || (item.is_dir ? "directory" : "file"),
                size: item.size,
                path: item.path || (path.endsWith('\\') ? path + item.name : path + '\\' + item.name)
            }));

            parsedEntries.sort((a, b) => {
                if (a.type === b.type) return a.name.localeCompare(b.name);
                return a.type === "directory" ? -1 : 1;
            });

            setEntries(parsedEntries);
            setCurrentPath(path);
        } catch (err: any) {
            setError(err.message || "Failed to list directory");
        } finally {
            setIsLoading(false);
        }
    };

    const readFile = async (entry: FileEntry) => {
        setIsLoading(true);
        try {
            const result = await client.callTool("file_ops", {
                operation: "read_file",
                path: entry.path || (currentPath + '\\' + entry.name)
            });

            const content = (result as any).content || (result as any).data || JSON.stringify(result, null, 2);
            setSelectedFile({ name: entry.name, content });
        } catch (err: any) {
            setError("Failed to read file: " + err.message);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (isConnected) {
            fetchDirectory(currentPath);
        }
    }, [isConnected]);

    const handleNavigate = (path: string) => {
        setHistory(prev => [...prev, currentPath]);
        fetchDirectory(path);
        setSelectedFile(null);
    };

    const handleBack = () => {
        if (history.length > 0) {
            const prev = history[history.length - 1];
            setHistory(h => h.slice(0, -1));
            fetchDirectory(prev);
            setSelectedFile(null);
        }
    };

    const getIcon = (entry: FileEntry) => {
        if (entry.type === "directory") return <Folder className="w-5 h-5 text-blue-400" />;
        if (entry.name.endsWith(".ts") || entry.name.endsWith(".tsx") || entry.name.endsWith(".js"))
            return <FileCode className="w-5 h-5 text-yellow-400" />;
        if (entry.name.endsWith(".png") || entry.name.endsWith(".jpg"))
            return <FileImage className="w-5 h-5 text-purple-400" />;
        return <File className="w-5 h-5 text-gray-400" />;
    };

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">File Browser</h1>
                    <p className="text-muted-foreground mt-2">Explore and manage files on the host system.</p>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => fetchDirectory(currentPath)}
                        className="p-2 hover:bg-accent rounded-md transition-colors"
                        title="Refresh"
                    >
                        <RefreshCw className={cn("w-5 h-5", isLoading && "animate-spin")} />
                    </button>
                </div>
            </div>

            <div className="flex-1 grid grid-cols-12 gap-6 min-h-0">
                <div className={cn("rounded-xl border border-border bg-card flex flex-col overflow-hidden", selectedFile ? "col-span-4" : "col-span-12")}>
                    <div className="p-4 border-b border-border flex items-center gap-2 bg-muted/30">
                        <button
                            onClick={handleBack}
                            disabled={history.length === 0}
                            className="p-1 hover:bg-background rounded disabled:opacity-30"
                        >
                            <ArrowLeft className="w-4 h-4" />
                        </button>
                        <div className="flex-1 font-mono text-xs truncate bg-background/50 px-2 py-1 rounded border border-border/50">
                            {currentPath}
                        </div>
                    </div>

                    <div className="flex-1 overflow-auto p-2">
                        {error && (
                            <div className="p-4 text-red-400 bg-red-400/10 rounded-lg m-2 text-sm flex gap-2">
                                <ArrowLeft className="w-5 h-5" />
                                {error}
                            </div>
                        )}

                        {!isConnected && (
                            <div className="text-center p-8 text-muted-foreground">
                                Connecting to server...
                            </div>
                        )}

                        {entries.map((entry, i) => (
                            <div
                                key={i}
                                onClick={() => entry.type === "directory" ? handleNavigate(entry.path) : readFile(entry)}
                                className="flex items-center gap-3 p-2 hover:bg-accent/50 rounded cursor-pointer transition-colors group"
                            >
                                {getIcon(entry)}
                                <span className="text-sm font-medium truncate flex-1">{entry.name}</span>
                                {entry.size !== undefined && (
                                    <span className="text-xs text-muted-foreground font-mono">
                                        {(entry.size / 1024).toFixed(1)} KB
                                    </span>
                                )}
                            </div>
                        ))}

                        {entries.length === 0 && !isLoading && !error && (
                            <div className="text-center p-8 text-muted-foreground text-sm">
                                Empty directory
                            </div>
                        )}
                    </div>
                </div>

                {selectedFile && (
                    <div className="col-span-8 rounded-xl border border-border bg-card flex flex-col overflow-hidden animate-in slide-in-from-right-4 duration-200">
                        <div className="p-4 border-b border-border flex items-center justify-between bg-muted/30">
                            <div className="font-medium flex items-center gap-2">
                                <FileCode className="w-4 h-4" />
                                {selectedFile.name}
                            </div>
                            <button onClick={() => setSelectedFile(null)} className="text-xs hover:underline">
                                Close
                            </button>
                        </div>
                        <div className="flex-1 overflow-auto bg-[#1e1e1e] p-4 font-mono text-sm leading-relaxed text-gray-300 whitespace-pre">
                            {selectedFile.content}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
