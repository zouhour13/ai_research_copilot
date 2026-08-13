"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BookOpen, Brain, Activity, X } from "lucide-react";
import { useAppStore } from "@/lib/store";
import SourcePanel from "@/components/sources/SourcePanel";
import MemoryViewer from "@/components/memory/MemoryViewer";
import AgentLogPanel from "@/components/agent/AgentLogPanel";

const TABS = [
  { id: "sources" as const, label: "Sources", icon: BookOpen },
  { id: "memory" as const, label: "Memory", icon: Brain },
  { id: "agent" as const, label: "Agent", icon: Activity },
];

export default function RightPanel() {
  const { rightPanelTab, setRightPanelTab, toggleRightPanel, messages } = useAppStore();
  const currentSources = messages.findLast((m) => m.role === "assistant" && m.sources?.length)?.sources ?? [];

  return (
    <div className="right-panel-inner">
      {/* Header */}
      <div className="right-panel-header">
        <div className="right-panel-tabs">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = rightPanelTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setRightPanelTab(tab.id)}
                className={`right-tab-btn ${isActive ? "right-tab-active" : ""}`}
              >
                <Icon size={13} />
                <span>{tab.label}</span>
                {tab.id === "sources" && currentSources.length > 0 && (
                  <span
                    className="ml-0.5 px-1.5 py-0.5 rounded-full text-[9px] font-bold"
                    style={{
                      background: isActive ? "var(--accent-glow)" : "var(--surface-hover)",
                      color: isActive ? "var(--accent)" : "var(--muted)",
                    }}
                  >
                    {currentSources.length}
                  </span>
                )}
              </button>
            );
          })}
        </div>
        <button
          onClick={toggleRightPanel}
          className="panel-close-btn"
          title="Close panel"
          aria-label="Close panel"
        >
          <X size={15} />
        </button>
      </div>

      {/* Content */}
      <div className="right-panel-content">
        <AnimatePresence mode="wait">
          {rightPanelTab === "sources" && (
            <motion.div
              key="sources"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
            >
              <SourcePanel sources={currentSources} />
            </motion.div>
          )}
          {rightPanelTab === "memory" && (
            <motion.div
              key="memory"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
            >
              <MemoryViewer />
            </motion.div>
          )}
          {rightPanelTab === "agent" && (
            <motion.div
              key="agent"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
            >
              <AgentLogPanel />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
