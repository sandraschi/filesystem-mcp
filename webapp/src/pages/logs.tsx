import { useEffect, useState, useRef } from "react";
import { Terminal, Download, Eraser, Filter } from "lucide-react";

type LogEntry = {
    id: string;
    timestamp: string;
    level: "INFO" | "WARN" | "ERROR" | "DEBUG";
    message: string;
    source: string;
};

export default function Logs() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Simulate log stream
    useEffect(() => {
        const interval = setInterval(() => {
            const levels: LogEntry["level"][] = ["INFO", "INFO", "DEBUG", "WARN", "INFO"];
            const sources = ["filesystem-mcp", "watcher", "api", "git-ops"];
            const messages = [
                "File change detected: /src/components/Logs.tsx",
                "API request received: GET /api/files",
                "Git status check completed",
                "Docker container statistics updated",
                "Connection established from 127.0.0.1",
            ];

            const newLog: LogEntry = {
                id: Math.random().toString(36).substr(2, 9),
                timestamp: new Date().toLocaleTimeString(),
                level: levels[Math.floor(Math.random() * levels.length)],
                source: sources[Math.floor(Math.random() * sources.length)],
                message: messages[Math.floor(Math.random() * messages.length)],
            };

            setLogs((prev) => [...prev.slice(-99), newLog]);
        }, 2000);

        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    const getLevelColor = (level: string) => {
        switch (level) {
            case "INFO": return "text-blue-400";
            case "WARN": return "text-yellow-400";
            case "ERROR": return "text-red-400";
            case "DEBUG": return "text-gray-400";
            default: return "text-foreground";
        }
    };

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">System Logs</h1>
                    <p className="text-muted-foreground mt-2">Real-time server log stream.</p>
                </div>
                <div className="flex gap-2">
                    <button className="p-2 hover:bg-accent rounded-md" title="Filter">
                        <Filter className="w-5 h-5" />
                    </button>
                    <button className="p-2 hover:bg-accent rounded-md" title="Clear Logs" onClick={() => setLogs([])}>
                        <Eraser className="w-5 h-5" />
                    </button>
                    <button className="p-2 hover:bg-accent rounded-md" title="Download">
                        <Download className="w-5 h-5" />
                    </button>
                </div>
            </div>

            <div className="flex-1 rounded-xl border border-border bg-black/90 font-mono text-sm shadow-inner overflow-hidden flex flex-col">
                <div className="flex items-center justify-between bg-muted/20 px-4 py-2 border-b border-border/50 text-xs text-muted-foreground">
                    <div className="flex items-center gap-2">
                        <Terminal className="w-4 h-4" />
                        <span>filesystem-mcp.log</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <span>Tail: On</span>
                        <span>Lines: {logs.length}</span>
                    </div>
                </div>

                <div className="flex-1 overflow-auto p-4 space-y-1" ref={scrollRef}>
                    {logs.length === 0 && (
                        <div className="text-muted-foreground text-center py-8 opacity-50">
                            Waiting for logs...
                        </div>
                    )}
                    {logs.map((log) => (
                        <div key={log.id} className="grid grid-cols-[80px_60px_100px_1fr] gap-4 hover:bg-white/5 px-2 py-0.5 rounded transition-colors">
                            <span className="text-muted-foreground/60">{log.timestamp}</span>
                            <span className={getLevelColor(log.level)}>{log.level}</span>
                            <span className="text-purple-400 truncate">{log.source}</span>
                            <span className="text-gray-300 break-all">{log.message}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
