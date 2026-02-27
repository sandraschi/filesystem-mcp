import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "@/components/theme-provider";
import Layout from "@/components/layout";
import Dashboard from "@/pages/dashboard";
import FileBrowser from "@/pages/file-browser";
import Tools from "@/pages/tools";
import GitOps from "@/pages/git-ops";
import DockerOps from "@/pages/docker-ops";
import Logs from "@/pages/logs";
import Settings from "@/pages/settings";
import Help from "@/pages/help";
import Chat from "@/pages/chat";
import Apps from "@/pages/apps";

import { McpProvider } from "@/shared/mcp-provider";

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <McpProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="chat" element={<Chat />} />
              <Route path="apps" element={<Apps />} />
              <Route path="files" element={<FileBrowser />} />
              <Route path="tools" element={<Tools />} />
              <Route path="git" element={<GitOps />} />
              <Route path="docker" element={<DockerOps />} />
              <Route path="logs" element={<Logs />} />
              <Route path="settings" element={<Settings />} />
              <Route path="help" element={<Help />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </McpProvider>
    </ThemeProvider>
  );
}

export default App;
