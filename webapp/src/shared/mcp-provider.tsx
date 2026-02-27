import React, { createContext, useContext, useEffect, useState } from 'react';
import { McpClient, McpTool } from './mcp-client';

type McpContextType = {
    client: McpClient;
    isConnected: boolean;
    tools: McpTool[];
    connect: () => Promise<void>;
};

const McpContext = createContext<McpContextType | null>(null);

export function McpProvider({ children }: { children: React.ReactNode }) {
    const [client] = useState(() => new McpClient());
    const [isConnected, setIsConnected] = useState(false);
    const [tools, setTools] = useState<McpTool[]>([]);

    const connect = async () => {
        try {
            await client.connect();
            setIsConnected(true);
            await client.refreshTools();
            setTools(client.getTools());
        } catch (e) {
            console.error('Failed to connect to MCP:', e);
            setIsConnected(false);
        }
    };

    useEffect(() => {
        // Auto-connect on mount
        connect();
    }, [client]);

    return (
        <McpContext.Provider value={{ client, isConnected, tools, connect }}>
            {children}
        </McpContext.Provider>
    );
}

export function useMcp() {
    const context = useContext(McpContext);
    if (!context) throw new Error('useMcp must be used within McpProvider');
    return context;
}
