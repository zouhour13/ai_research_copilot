"use client";

import { useAppStore } from "@/lib/store";
import Sidebar from "./Sidebar";
import ChatWindow from "./ChatWindow";
import ChatInput from "./ChatInput";
import RightPanel from "./layout/RightPanel";
import AgentActivityBar from "./agent/AgentActivityBar";
import {
  Globe,
  MessageSquare,
  Plus,
  Menu,
  PanelRight,
  Cpu,
  Zap,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function AppLayout() {
  const {
    sessions,
    activeSessionId,
    isSidebarOpen,
    isResearchMode,
    isRightPanelOpen,
    currentProvider,
    currentModel,
    toggleSidebar,
    toggleRightPanel,
    setRightPanelTab,
    createNewSession,
    messages,
  } = useAppStore();

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const latestSources = messages.findLast(
    (m) => m.role === "assistant" && m.sources?.length
  )?.sources ?? [];

  const handleSourcesClick = () => {
    setRightPanelTab("sources");
    if (!isRightPanelOpen) toggleRightPanel();
  };

  // Short model label for topbar badge
  const modelLabel = currentModel.split("-").slice(0, 2).join("-");

  return (
    <div className="app-root">
      {/* ── Sidebar ─────────────────────────────────────────────── */}
      <AnimatePresence initial={false}>
        {isSidebarOpen && (
          <motion.aside
            key="sidebar"
            className="sidebar-panel"
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 268, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: [0.4, 0, 0.2, 1] }}
          >
            <Sidebar />
          </motion.aside>
        )}
      </AnimatePresence>

      {/* ── Main content ────────────────────────────────────────── */}
      <main className="main-panel">
        {/* ── Topbar ──────────────────────────────────────────────── */}
        <header className="topbar">
          <div className="topbar-left">
            {/* Sidebar toggle / logo mark */}
            <button
              onClick={toggleSidebar}
              title={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
              className="icon-btn"
              aria-label={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
            >
              {isSidebarOpen ? (
                <Menu size={16} />
              ) : (
                <div className="brand-mark" role="presentation">
                  <Cpu size={14} className="text-white" />
                </div>
              )}
            </button>

            {/* Brand / Session name */}
            <div className="topbar-title">
              {activeSession ? (
                <>
                  {isResearchMode ? (
                    <Globe
                      size={13}
                      className="topbar-mode-icon research flex-shrink-0"
                    />
                  ) : (
                    <MessageSquare
                      size={13}
                      className="topbar-mode-icon flex-shrink-0"
                    />
                  )}
                  <h1 className="topbar-session-name">
                    {activeSession.title || "New Chat"}
                  </h1>
                  {isResearchMode && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-accent/10 text-accent border border-accent/20 flex-shrink-0">
                      <Globe size={9} />
                      Research
                    </span>
                  )}
                </>
              ) : (
                <h1 className="topbar-brand">Nexus Research</h1>
              )}
            </div>
          </div>

          <div className="topbar-right">
            {/* Model badge */}
            <div className="topbar-model-badge" title={`${currentProvider} / ${currentModel}`}>
              <span className="topbar-model-badge-dot" />
              <span className="capitalize">{currentProvider}</span>
              <span className="text-muted-2 hidden sm:inline">·</span>
              <span className="hidden sm:inline opacity-70">{modelLabel}</span>
            </div>

            {/* Sources button */}
            {latestSources.length > 0 && (
              <motion.button
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                onClick={handleSourcesClick}
                className="topbar-sources-btn"
                title="View sources"
              >
                <Globe size={11} />
                {latestSources.length} source{latestSources.length !== 1 ? "s" : ""}
              </motion.button>
            )}

            {/* Right panel toggle */}
            <button
              onClick={toggleRightPanel}
              className={`icon-btn ${isRightPanelOpen ? "icon-btn-active" : ""}`}
              title="Toggle right panel"
              aria-label="Toggle right panel"
            >
              <PanelRight size={16} />
            </button>

            <div className="topbar-divider" />

            {/* New chat */}
            <motion.button
              whileTap={{ scale: 0.95 }}
              whileHover={{ scale: 1.02 }}
              onClick={createNewSession}
              className="new-chat-btn"
              id="new-chat-topbar-btn"
            >
              <Plus size={13} />
              <span>New Chat</span>
            </motion.button>
          </div>
        </header>

        {/* Chat */}
        <ChatWindow />

        {/* Agent activity bar */}
        <AgentActivityBar />

        {/* Input */}
        <ChatInput />
      </main>

      {/* ── Right panel ─────────────────────────────────────────── */}
      <AnimatePresence initial={false}>
        {isRightPanelOpen && (
          <motion.aside
            key="right-panel"
            className="right-panel"
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 340, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: [0.4, 0, 0.2, 1] }}
          >
            <RightPanel />
          </motion.aside>
        )}
      </AnimatePresence>
    </div>
  );
}
