import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Wrench, AlertCircle } from "lucide-react";
import { useMcp } from "@/shared/mcp-provider";
import { cn } from "@/shared/utils";
import { Link } from "react-router-dom";

type Message = {
    id: string;
    role: "user" | "assistant" | "system";
    content: string;
    toolCall?: { name: string; args: any; result?: any };
    error?: string;
};

interface LlmConfig {
    provider: string;
    baseUrl: string;
    apiKey: string;
    model: string;
}

export default function Chat() {
    const { client, isConnected, tools } = useMcp();
    const [messages, setMessages] = useState<Message[]>([
        { id: "1", role: "assistant", content: "Hello! I'm connected to your filesystem. Configure your Local LLM in settings to start chatting." }
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const [config, setConfig] = useState<LlmConfig | null>(null);

    useEffect(() => {
        const saved = localStorage.getItem("llm_config");
        if (saved) {
            try {
                setConfig(JSON.parse(saved));
            } catch (e) {
                console.error("Invalid config");
            }
        }
    }, []);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const callLlm = async (messages: Message[], currentConfig: LlmConfig) => {
        if (!currentConfig) throw new Error("LLM not configured");

        const apiMessages = messages.map(m => ({
            role: m.role,
            content: m.content
        }));

        // Create valid tools definition for OpenAI format (Ollama supports this)
        let toolsBody = undefined;
        if (tools.length > 0) {
            toolsBody = tools.map(t => ({
                type: "function",
                function: {
                    name: t.name,
                    description: t.description,
                    parameters: t.inputSchema
                }
            }));
        }

        const body: any = {
            model: currentConfig.model,
            messages: apiMessages,
            stream: false, // Simple non-streaming for now
        };

        if (toolsBody) {
            body.tools = toolsBody;
        }

        const headers: Record<string, string> = {
            'Content-Type': 'application/json'
        };
        if (currentConfig.apiKey) {
            headers['Authorization'] = `Bearer ${currentConfig.apiKey}`;
            headers['x-api-key'] = currentConfig.apiKey; // Anthropic sometimes needs this
        }

        // Adjust endpoint based on provider
        let endpoint = `${currentConfig.baseUrl}/chat/completions`; // Default OpenAI/Ollama
        if (currentConfig.provider === 'anthropic') endpoint = `${currentConfig.baseUrl}/messages`;
        // Anthropic has different body format, but let's assume OpenAI compat shim or standard Ollama/LM Studio for this iteration

        console.log("Calling LLM:", endpoint, body);

        const response = await fetch(endpoint, {
            method: 'POST',
            headers,
            body: JSON.stringify(body)
        });

        if (!response.ok) {
            const text = await response.text();
            throw new Error(`LLM Error (${response.status}): ${text}`);
        }

        return await response.json();
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        // Use default config if none exists
        const activeConfig = config || {
            provider: "ollama",
            baseUrl: "http://localhost:11434",
            apiKey: "",
            model: "llama3.2:1b"
        };

        const userMsg: Message = {
            id: Date.now().toString(),
            role: "user",
            content: input
        };

        const newHistory = [...messages, userMsg];
        setMessages(newHistory);
        setInput("");
        setIsLoading(true);

        try {
            const data = await callLlm(newHistory, activeConfig);
            console.log("LLM Response:", data);

            const choice = data.choices?.[0];
            const message = choice?.message;

            if (message) {
                // Check for tool calls
                if (message.tool_calls && message.tool_calls.length > 0) {
                    const toolCall = message.tool_calls[0];
                    const fnName = toolCall.function.name;
                    const fnArgs = JSON.parse(toolCall.function.arguments);

                    setMessages(prev => [...prev, {
                        id: Date.now().toString(),
                        role: "assistant",
                        content: message.content || "Executing tool...",
                        toolCall: { name: fnName, args: fnArgs }
                    }]);

                    // Execute tool
                    try {
                        const result = await client.callTool(fnName, fnArgs);

                        // In a real loop, we would send this result back to LLM
                        // For this demo, we just show the result
                        setMessages(prev => {
                            const last = prev[prev.length - 1];
                            if (last.toolCall) {
                                last.toolCall.result = result;
                            }
                            return [...prev]; // Force update
                        });

                        // Optional: Call LLM again with result? 
                        // For simple "one-shot" demo, we stop here. 
                        // To implement full loop, we'd append tool response and recurse.

                    } catch (err: any) {
                        setMessages(prev => [...prev, {
                            id: Date.now().toString(),
                            role: "system",
                            content: `Tool execution failed: ${err.message}`,
                            error: err.message
                        }]);
                    }

                } else {
                    setMessages(prev => [...prev, {
                        id: Date.now().toString(),
                        role: "assistant",
                        content: message.content
                    }]);
                }
            } else {
                // Fallback/Error
                throw new Error("Invalid response format from LLM");
            }

        } catch (error: any) {
            console.error(error);
            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: "assistant",
                content: "Sorry, I encountered an error communicating with the LLM.",
                error: error.message
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-8rem)]">
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Chat</h1>
                    <p className="text-muted-foreground">Interact with your filesystem using {config?.provider || "Local LLM"}.</p>
                </div>
                <div className="flex items-center gap-2">
                    {!config && (
                        <Link to="/settings" className="text-yellow-500 flex items-center gap-1 text-sm bg-yellow-500/10 px-3 py-1 rounded-full">
                            <AlertCircle className="w-4 h-4" />
                            Configure LLM
                        </Link>
                    )}
                    <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${isConnected ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500"}`}>
                        <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`} />
                        {isConnected ? "MCP Connected" : "MCP Disconnected"}
                    </div>
                </div>
            </div>

            <div className="flex-1 rounded-xl border border-border bg-card shadow-sm overflow-hidden flex flex-col">
                <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef}>
                    {messages.map((msg) => (
                        <div key={msg.id} className={cn("flex gap-3 max-w-[80%]", msg.role === "user" ? "ml-auto flex-row-reverse" : "")}>
                            <div className={cn("w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                                msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground")}>
                                {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                            </div>
                            <div className={cn("rounded-lg p-3 text-sm",
                                msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted")}>
                                {msg.error && (
                                    <div className="text-red-400 font-bold mb-1 flex items-center gap-1">
                                        <AlertCircle className="w-3 h-3" /> Error
                                    </div>
                                )}
                                <p className="whitespace-pre-wrap">{msg.content}</p>

                                {msg.toolCall && (
                                    <div className="mt-2 p-2 bg-black/10 rounded text-xs font-mono overflow-x-auto">
                                        <div className="flex items-center gap-1 mb-1 text-xs opacity-70">
                                            <Wrench className="w-3 h-3" />
                                            Tool: {msg.toolCall.name}
                                        </div>
                                        <div className="mb-1 text-blue-300">
                                            Args: {JSON.stringify(msg.toolCall.args)}
                                        </div>
                                        {msg.toolCall.result && (
                                            <div className="text-green-300 border-t border-white/10 pt-1 mt-1">
                                                Result: {JSON.stringify(msg.toolCall.result).substring(0, 300)}...
                                            </div>
                                        )}
                                    </div>
                                )}
                                {msg.error && (
                                    <div className="mt-2 text-xs opacity-70 border-t border-white/20 pt-1">
                                        {msg.error}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex gap-3">
                            <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center shrink-0">
                                <Bot className="w-4 h-4 animate-pulse" />
                            </div>
                            <div className="bg-muted rounded-lg p-3 text-sm">
                                <span className="animate-pulse">Thinking...</span>
                            </div>
                        </div>
                    )}
                </div>

                <div className="p-4 border-t border-border bg-card/50">
                    <form onSubmit={handleSubmit} className="flex gap-2">
                        <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={config ? "Ask to list files, read code, or check status..." : "Enter your message (Defaults to Ollama/Llama3.2:1b)..."}
                            disabled={!isConnected || isLoading}
                            className="flex-1 bg-background border border-input rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                        />
                        <button
                            type="submit"
                            disabled={!isConnected || isLoading || !input.trim()}
                            className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            <Send className="w-4 h-4" />
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}
