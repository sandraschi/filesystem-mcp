import { EventSourcePolyfill } from 'event-source-polyfill';

export type McpTool = {
    name: string;
    description?: string;
    inputSchema: any;
};

export type McpCallResult = {
    content: Array<{ type: string; text?: string; data?: string; mimeType?: string }>;
    isError?: boolean;
};

export class McpClient {
    private sse: EventSourcePolyfill | null = null;
    private endpoint: string | null = null;
    private sessionId: string | null = null;
    private tools: McpTool[] = [];
    private onToolsChanged: ((tools: McpTool[]) => void)[] = [];

    constructor(private baseUrl: string = '/mcp') { }

    async connect() {
        return new Promise<void>((resolve, reject) => {
            // FastMCP uses /sse for the stream
            const sseUrl = `${this.baseUrl}/sse`;
            console.log('Connecting to MCP SSE:', sseUrl);

            this.sse = new EventSourcePolyfill(sseUrl);

            this.sse.onmessage = (event: MessageEvent) => {
                try {
                    const data = JSON.parse(event.data);

                    if (event.type === 'endpoint') {
                        this.endpoint = data;
                        console.log('MCP Endpoint discovered:', this.endpoint);
                        // Once we have an endpoint, we can identify and list tools
                        this.initializeSession().then(resolve).catch(reject);
                    } else if (event.type === 'initialization') {
                        // Handle initialization if distinct from endpoint
                    }
                } catch (e) {
                    console.error('Failed to parse SSE message:', e);
                }
            };

            this.sse.onerror = (e: any) => {
                console.error('MCP SSE Error:', e);
                // Don't reject immediately on error if we are already connected, but do for initial connect
                if (!this.endpoint) reject(e);
            };

            this.sse.addEventListener('endpoint', (e: any) => {
                this.endpoint = e.data;
                console.log('MCP Endpoint event:', this.endpoint);
                this.initializeSession().then(resolve).catch(reject);
            });
        });
    }

    private async initializeSession() {
        if (!this.endpoint) throw new Error('No endpoint received from SSE');
        await this.refreshTools();
    }

    async callTool(name: string, args: any): Promise<McpCallResult> {
        if (!this.endpoint) throw new Error('Not connected');

        const response = await fetch(`${this.baseUrl}/messages?sessionId=${this.sessionId || ''}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0',
                id: crypto.randomUUID(),
                method: 'tools/call',
                params: {
                    name,
                    arguments: args
                }
            })
        });

        if (!response.ok) {
            throw new Error(`MCP Call Failed: ${response.statusText}`);
        }

        const result = await response.json();
        if (result.error) {
            throw new Error(result.error.message);
        }

        return result.result;
    }

    async refreshTools() {
        if (!this.endpoint) return;

        // Standard list_tools call
        const response = await fetch(`${this.baseUrl}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0',
                id: crypto.randomUUID(),
                method: 'tools/list',
                params: {}
            })
        });

        const data = await response.json();
        if (data.result && data.result.tools) {
            this.tools = data.result.tools;
            this.notifyToolsChanged();
        }
    }

    subscribeTools(callback: (tools: McpTool[]) => void) {
        this.onToolsChanged.push(callback);
        callback(this.tools);
        return () => {
            this.onToolsChanged = this.onToolsChanged.filter(cb => cb !== callback);
        };
    }

    private notifyToolsChanged() {
        this.onToolsChanged.forEach(cb => cb(this.tools));
    }

    getTools() {
        return this.tools;
    }
}

export const mcpClient = new McpClient();
