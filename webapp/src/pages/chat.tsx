import { AlertCircle, Bot, Download, Eraser, Send, Sparkles, User } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useMcp } from "@/shared/mcp-provider";
import { cn } from "@/shared/utils";

type ChatRole = "user" | "assistant" | "system";

type Message = {
  id: string;
  role: ChatRole;
  content: string;
  ts?: string;
  error?: boolean;
};

interface LlmConfig {
  provider: string;
  baseUrl: string;
  apiKey: string;
  model: string;
}

const HISTORY_KEY = "filesystem-mcp-chat-history";
const PERSONALITY_KEY = "filesystem-mcp-chat-personality";
const MAX_MESSAGES = 100;

const PERSONALITIES: Record<string, { label: string; prompt: string }> = {
  "research-assistant": {
    label: "Research Assistant",
    prompt:
      "You are a careful research assistant. When answering questions about files, code, or system state, ground your answer in the facts available. Be precise, cite file paths when relevant, and keep responses structured with short paragraphs or bullets.",
  },
  "expert-reviewer": {
    label: "Expert Reviewer",
    prompt:
      "You are a senior code and systems reviewer. Critically evaluate what you see, point out risks, performance issues, and security concerns. Be direct and technical. Suggest concrete improvements with reasoning.",
  },
  "quick-summarizer": {
    label: "Quick Summarizer",
    prompt:
      "You are a concise summarizer. Respond in 2-3 sentences unless a longer answer is explicitly requested. Prefer bullet points for multi-part answers. No filler.",
  },
  custom: {
    label: "Custom",
    prompt: "",
  },
};

const EXAMPLE_PROMPTS = [
  {
    group: "Files",
    prompts: [
      "List the largest files in my home directory",
      "Find duplicate files in D:/Dev/repos",
      "Show me the structure of D:/Dev/repos/arxiv-mcp",
    ],
  },
  {
    group: "Search",
    prompts: [
      "Search for files containing 'assfix' in D:/Dev/repos",
      "Compare two files side by side",
      "Extract error lines from a log file",
    ],
  },
  {
    group: "Git",
    prompts: [
      "Show the git status of the current repo",
      "What changed in the last 5 commits?",
      "Clone a repository and show its structure",
    ],
  },
  {
    group: "System",
    prompts: [
      "How much memory is in use right now?",
      "Show me the top 5 processes by CPU",
      "Check disk usage per partition",
    ],
  },
];

const DEFAULT_PROMPT =
  "You are an assistant for Filesystem MCP, a server that manages files, directories, Git repositories, Docker containers, and system monitoring through concurrency-safe tools. Answer questions about the user's files and system. When the user asks for file operations, suggest using the File Browser page or describe the MCP tool call that would achieve it.";

const CONTEXT_PRESETS: Record<string, string> = {
  "code-review":
    "Act as a senior code reviewer. Walk through the repository at D:/Dev/repos and identify quality, security, and performance issues. Report findings with file paths and concrete suggestions.",
  "log-analysis":
    "Analyze the log files in D:/Dev/repos/filesystem-mcp/logs (and the repo root *.log files). Identify anomalies, error patterns, and root causes. Summarize with severity ordering.",
  "system-health":
    "Run a system health check: CPU, memory, disk usage, and top processes. Report whether the system is healthy or degraded and what to address.",
  "large-files":
    "Find the largest files on D:/Dev and suggest which ones are safe cleanup candidates. Show sizes and paths.",
  "disk-audit":
    "Audit disk usage per directory under D:/Dev/repos. Identify the biggest consumers and recommend cleanup targets.",
};

function formatTimestamp(ts?: string): string {
  if (!ts) return "";
  try {
    return new Date(ts).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export default function Chat() {
  const { isConnected, tools } = useMcp();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [config, setConfig] = useState<LlmConfig | null>(null);
  const [personality, setPersonality] = useState(() => localStorage.getItem(PERSONALITY_KEY) || "research-assistant");
  const [skillPrompt, setSkillPrompt] = useState<string | null>(null);
  const [customPrompt, setCustomPrompt] = useState("");
  const [showExamples, setShowExamples] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const mountedRef = useRef(false);

  useEffect(() => {
    const saved = localStorage.getItem("llm_config");
    if (saved) {
      try {
        setConfig(JSON.parse(saved));
      } catch {
        // ignore corrupt config
      }
    }
  }, []);

  // Restore history + discover skills on mount
  useEffect(() => {
    const saved = localStorage.getItem(HISTORY_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved) as Message[];
        if (Array.isArray(parsed)) setMessages(parsed.slice(-MAX_MESSAGES));
      } catch {
        // ignore corrupt history
      }
    }
    mountedRef.current = true;
    const params = new URLSearchParams(window.location.search);
    const context = params.get("context");
    if (context && CONTEXT_PRESETS[context]) {
      setInput(CONTEXT_PRESETS[context]);
      setShowExamples(false);
    }
    (async () => {
      try {
        const r = await fetch(`/api/skills`, {
          signal: AbortSignal.timeout(4000),
        });
        if (r.ok) {
          const data = await r.json();
          const skills = Array.isArray(data.skills) ? data.skills : [];
          if (skills.length > 0) {
            setSkillPrompt(
              `The following skill describes this server's capabilities:\n${skills.map((s: { name?: string }) => s.name ?? "").join(", ")}`,
            );
          }
        }
      } catch {
        // backend not reachable yet — default prompt covers it
      }
    })();
  }, []);

  useEffect(() => {
    if (mountedRef.current && messages.length > 0) {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(messages.slice(-MAX_MESSAGES)));
    }
  }, [messages]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: scrollRef is a stable ref; scroll after messages/isLoading updates
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const systemPrompt = useMemo(() => {
    const base = skillPrompt ?? DEFAULT_PROMPT;
    if (personality === "custom") return customPrompt || base;
    const persona = PERSONALITIES[personality]?.prompt ?? "";
    return `${base}\n\n---\n\n## Role\n${persona}`;
  }, [skillPrompt, personality, customPrompt]);

  const callLlm = useCallback(
    async (history: Message[]): Promise<{ content: string; toolCalls?: unknown[] }> => {
      const activeConfig =
        config ??
        ({
          provider: "ollama",
          baseUrl: "http://localhost:11434",
          apiKey: "",
          model: "llama3.2:1b",
        } as LlmConfig);

      const apiMessages = [
        { role: "system", content: systemPrompt },
        ...history.filter((m) => m.role !== "system").map((m) => ({ role: m.role, content: m.content })),
      ];

      const toolsBody = tools.slice(0, 40).map((t) => ({
        type: "function",
        function: {
          name: t.name,
          description: t.description,
          parameters: t.inputSchema,
        },
      }));

      const body = {
        provider: {
          id: activeConfig.provider,
          name: activeConfig.provider,
          type: activeConfig.provider,
          baseUrl: activeConfig.baseUrl,
          apiKey: activeConfig.apiKey,
          enabled: true,
        },
        model: activeConfig.model,
        messages: apiMessages,
        tools: toolsBody.length > 0 ? toolsBody : null,
      };

      const r = await fetch("/api/llm/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(90000),
      });
      if (!r.ok) {
        const text = await r.text();
        throw new Error(`LLM Error (${r.status}): ${text.slice(0, 300)}`);
      }
      return await r.json();
    },
    [config, systemPrompt, tools],
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !isConnected) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      ts: new Date().toISOString(),
    };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setInput("");
    setShowExamples(false);
    setIsLoading(true);

    try {
      const { content, toolCalls } = await callLlm(newHistory);
      let assistantText = content;
      if ((toolCalls ?? []).length > 0) {
        const first = toolCalls![0] as {
          function?: { name?: string; arguments?: string };
        };
        const name = first?.function?.name ?? "tool";
        assistantText = `\n\n[Tool call: ${name}]`;
        if (content) assistantText = content + assistantText;
      }
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: assistantText || "*(empty response from LLM)*",
          ts: new Date().toISOString(),
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: `Sorry, I hit an error talking to the LLM: ${err instanceof Error ? err.message : String(err)}`,
          ts: new Date().toISOString(),
          error: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = () => {
    if (messages.length === 0) return;
    const text = messages.map((m) => `[${formatTimestamp(m.ts)}] ${m.role.toUpperCase()}: ${m.content}`).join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `filesystem-mcp-chat-${new Date().toISOString().replace(/[:.]/g, "-")}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClear = () => {
    setMessages([]);
    localStorage.removeItem(HISTORY_KEY);
  };

  const changePersonality = (value: string) => {
    setPersonality(value);
    localStorage.setItem(PERSONALITY_KEY, value);
  };

  return (
    <div data-testid="chat-page" className="flex flex-col h-[calc(100vh-8rem)]">
      <div data-testid="chat-controls" className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Chat</h1>
          <p className="text-muted-foreground">
            Interact with your filesystem using {config?.provider || "a local LLM"}.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <select
            data-testid="personality-select"
            value={personality}
            onChange={(e) => changePersonality(e.target.value)}
            className="bg-zinc-800 text-zinc-100 border border-zinc-600 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            aria-label="Personality"
          >
            {Object.entries(PERSONALITIES).map(([id, p]) => (
              <option key={id} value={id}>
                {p.label}
              </option>
            ))}
          </select>
          <button
            data-testid="chat-export"
            onClick={handleExport}
            disabled={messages.length === 0}
            title="Export conversation"
            className="p-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Download className="h-4 w-4" />
          </button>
          <button
            data-testid="chat-clear"
            onClick={handleClear}
            disabled={messages.length === 0}
            title="Clear conversation"
            className="p-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Eraser className="h-4 w-4" />
          </button>
          <div
            className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${isConnected ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500"}`}
          >
            <span className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`} />
            {isConnected ? "MCP Connected" : "MCP Disconnected"}
          </div>
        </div>
      </div>

      {personality === "custom" && (
        <textarea
          value={customPrompt}
          onChange={(e) => setCustomPrompt(e.target.value)}
          placeholder="Custom system prompt (fallback: server default)"
          rows={3}
          className="mb-3 w-full bg-zinc-800 text-zinc-100 border border-zinc-600 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        />
      )}

      <div className="flex-1 rounded-xl border border-border bg-card shadow-sm overflow-hidden flex flex-col">
        <div data-testid="chat-messages" className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef}>
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center gap-2 text-muted-foreground">
              <Bot className="h-10 w-10" />
              <p className="font-medium text-foreground">Chat with your filesystem</p>
              <p className="text-sm max-w-md">
                Ask about files, directories, Docker containers, or system state. Responses use your local LLM (Ollama /
                LM Studio) configured in Settings.
              </p>
              {!config && (
                <Link
                  to="/settings"
                  className="mt-2 text-yellow-500 flex items-center gap-1 text-sm bg-yellow-500/10 px-3 py-1 rounded-full hover:bg-yellow-500/20 transition-colors"
                >
                  <AlertCircle className="w-4 h-4" /> Configure LLM
                </Link>
              )}
            </div>
          )}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={cn("flex gap-3 max-w-[85%]", msg.role === "user" ? "ml-auto flex-row-reverse" : "")}
            >
              <div
                className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                  msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground",
                )}
              >
                {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>
              <div
                className={cn(
                  "rounded-lg p-3 text-sm",
                  msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted",
                )}
              >
                {msg.error && <div className="text-red-400 font-bold mb-1">Error</div>}
                <p className="whitespace-pre-wrap">{msg.content}</p>
                {msg.ts && <div className="mt-1 text-xs opacity-50">{formatTimestamp(msg.ts)}</div>}
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

        {showExamples && messages.length === 0 && (
          <div data-testid="example-prompts" className="px-4 pb-3 border-t border-border/50">
            <p className="text-xs text-muted-foreground uppercase tracking-wide pt-3 pb-2 flex items-center gap-1">
              <Sparkles className="h-3 w-3" /> Try asking
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {EXAMPLE_PROMPTS.map((group) => (
                <div key={group.group}>
                  <p className="text-xs font-medium text-primary/80 mb-1">{group.group}</p>
                  <div className="space-y-1">
                    {group.prompts.map((p) => (
                      <button
                        key={p}
                        onClick={() => setInput(p)}
                        className="block w-full text-left rounded-md border border-border bg-background/60 px-3 py-2 text-sm hover:border-primary/50 hover:bg-accent/50 transition-colors"
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="p-4 border-t border-border bg-card/50">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              data-testid="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about files, search, git, or system status..."
              disabled={!isConnected || isLoading}
              className="flex-1 bg-background border border-input rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <button
              data-testid="chat-send"
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
