"use client";

import { useAppStore } from "@/lib/store";
import Sidebar from "@/components/Sidebar";
import RightPanel from "@/components/layout/RightPanel";
import ChatWindow from "@/components/ChatWindow";
import ChatInput from "@/components/ChatInput";
import AgentActivityBar from "@/components/agent/AgentActivityBar";

export default function AppShell() {
  const { isSidebarOpen, isRightPanelOpen } = useAppStore();

  return (
    <div className="app-shell">
      {/* Left sidebar */}
      <aside className={`sidebar-panel ${isSidebarOpen ? "sidebar-open" : "sidebar-closed"}`}>
        <Sidebar />
      </aside>

      {/* Main content */}
      <main className="main-panel">
        <ChatWindow />
        <AgentActivityBar />
        <ChatInput />
      </main>

      {/* Right panel */}
      <aside className={`right-panel ${isRightPanelOpen ? "right-panel-open" : "right-panel-closed"}`}>
        <RightPanel />
      </aside>
    </div>
  );
}
