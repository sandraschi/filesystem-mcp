export type McpTool = {
  name: string;
  description?: string;
  inputSchema: any;
};

export type McpCallResult = {
  content: Array<{
    type: string;
    text?: string;
    data?: string;
    mimeType?: string;
  }>;
  isError?: boolean;
};

const isProduction =
  import.meta.env.PROD || (typeof window !== "undefined" && !window.location.hostname.includes("localhost"));

function getMCPBaseUrl(): string {
  // Always talk to the backend directly (cross-origin is covered by fleet CORS).
  // The Vite proxy path drops response headers (e.g. mcp-session-id) in some
  // dev setups, which breaks streamable-HTTP session handshakes.
  return "http://127.0.0.1:10742/mcp";
}

type JsonRpcResponse = {
  jsonrpc: string;
  id: string | number | null;
  result?: any;
  error?: { code: number; message: string };
};

export class McpClient {
  private sessionId: string | null = null;
  private tools: McpTool[] = [];
  private onToolsChanged: ((tools: McpTool[]) => void)[] = [];
  private connecting: Promise<void> | null = null;

  constructor(private baseUrl = getMCPBaseUrl()) {}

  private async post(payload: Record<string, unknown>, expectResult = true): Promise<JsonRpcResponse> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json, text/event-stream",
    };
    if (this.sessionId) headers["Mcp-Session-Id"] = this.sessionId;

    const response = await fetch(this.baseUrl, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`MCP request failed: HTTP ${response.status} ${response.statusText}`);
    }

    const nextSession = response.headers.get("mcp-session-id");
    if (nextSession) this.sessionId = nextSession;

    const text = await response.text();
    if (!text.trim()) return { jsonrpc: "2.0", id: null, result: undefined };

    // Streamable HTTP may return SSE events; parse the first JSON line if so.
    if (text.trimStart().startsWith("event:")) {
      const lines = text.split("\n").filter((l) => l.startsWith("data:"));
      for (const line of lines) {
        try {
          return JSON.parse(line.slice(5).trim());
        } catch {
          // skip malformed SSE data frames
        }
      }
      return { jsonrpc: "2.0", id: null, result: undefined };
    }

    return JSON.parse(text) as JsonRpcResponse;
  }

  async connect() {
    // Serialize concurrent connect() calls (React StrictMode double-mounts in dev)
    // so two in-flight initializes cannot clobber each other's session id.
    if (this.connecting) return this.connecting;
    this.connecting = this.doConnect().finally(() => {
      this.connecting = null;
    });
    return this.connecting;
  }

  private async doConnect() {
    const response = await this.post({
      jsonrpc: "2.0",
      id: "init-1",
      method: "initialize",
      params: {
        protocolVersion: "2025-11-25",
        capabilities: {},
        clientInfo: { name: "filesystem-mcp-webapp", version: "2.2.0" },
      },
    });

    if (response.error) {
      throw new Error(`MCP initialize failed: ${response.error.message}`);
    }

    // Notify the server the session is initialized (notification, no id).
    await this.post({ jsonrpc: "2.0", method: "notifications/initialized" }, false).catch(() => {
      // notification failures are non-fatal
    });

    await this.refreshTools();
  }

  async callTool(name: string, args: any): Promise<McpCallResult> {
    const response = await this.post({
      jsonrpc: "2.0",
      id: crypto.randomUUID(),
      method: "tools/call",
      params: { name, arguments: args },
    });

    if (response.error) {
      throw new Error(response.error.message);
    }
    return response.result as McpCallResult;
  }

  async refreshTools() {
    const response = await this.post({
      jsonrpc: "2.0",
      id: crypto.randomUUID(),
      method: "tools/list",
      params: {},
    });

    if (response.error) {
      throw new Error(`MCP tools/list failed: ${response.error.message}`);
    }
    if (response.result?.tools) {
      this.tools = response.result.tools;
      this.notifyToolsChanged();
    }
  }

  subscribeTools(callback: (tools: McpTool[]) => void) {
    this.onToolsChanged.push(callback);
    callback(this.tools);
    return () => {
      this.onToolsChanged = this.onToolsChanged.filter((cb) => cb !== callback);
    };
  }

  private notifyToolsChanged() {
    this.onToolsChanged.forEach((cb) => {
      cb(this.tools);
    });
  }

  getTools() {
    return this.tools;
  }
}

export const mcpClient = new McpClient();
