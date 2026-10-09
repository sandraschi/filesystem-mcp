import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "@/components/layout";
import { ThemeProvider } from "@/components/theme-provider";
import Apps from "@/pages/apps";
import Chat from "@/pages/chat";
import Dashboard from "@/pages/dashboard";
import DockerOps from "@/pages/docker-ops";
import FileBrowser from "@/pages/file-browser";
import GitOps from "@/pages/git-ops";
import Help from "@/pages/help";
import Inbox from "@/pages/inbox";
import Logs from "@/pages/logs";
import Settings from "@/pages/settings";
import Skills from "@/pages/skills";
import Tools from "@/pages/tools";

import { McpProvider } from "@/shared/mcp-provider";

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <McpProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="inbox" element={<Inbox />} />
              <Route path="chat" element={<Chat />} />
              <Route path="apps" element={<Apps />} />
              <Route path="files" element={<FileBrowser />} />
              <Route path="tools" element={<Tools />} />
              <Route path="skills" element={<Skills />} />
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
