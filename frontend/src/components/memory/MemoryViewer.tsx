"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Brain, Search, Trash2, RefreshCw } from "lucide-react";
import { useAppStore } from "@/lib/store";
import { resetMemory } from "@/lib/api";
import { toast } from "sonner";

export default function MemoryViewer() {
  const { activeSessionId, memoryItems, memoryLoading, loadMemory } = useAppStore();
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    if (activeSessionId) loadMemory(activeSessionId);
  }, [activeSessionId, loadMemory]);

  const handleSearch = () => {
    if (activeSessionId) loadMemory(activeSessionId, searchQuery);
  };

  const handleReset = async () => {
    if (!activeSessionId) return;
    try {
      await resetMemory(activeSessionId);
      await loadMemory(activeSessionId);
      toast.success("Memory cleared for this session");
    } catch {
      toast.error("Failed to clear memory");
    }
  };

  if (!activeSessionId) {
    return (
      <div className="panel-empty">
        <Brain size={30} className="panel-empty-icon" />
        <p>Select a conversation to view its memory.</p>
      </div>
    );
  }

  return (
    <div className="memory-viewer">
      {/* Search bar */}
      <div className="memory-search">
        <div className="relative flex-1">
          <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: "var(--muted-2)" }} />
          <input
            type="text"
            placeholder="Search memory…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="memory-search-input pl-8"
          />
        </div>
        <button
          onClick={handleSearch}
          className="memory-search-btn"
          title="Search"
          aria-label="Search memory"
        >
          <RefreshCw size={13} />
        </button>
      </div>

      {/* Count + reset */}
      <div className="memory-meta">
        <span className="memory-count flex items-center gap-1.5">
          <Brain size={11} style={{ color: "var(--accent-2)" }} />
          {memoryLoading ? "Loading…" : `${memoryItems.length} memory ${memoryItems.length === 1 ? "summary" : "summaries"}`}
        </span>
        {memoryItems.length > 0 && (
          <button onClick={handleReset} className="memory-reset-btn" title="Clear memory">
            <Trash2 size={12} />
            <span>Clear</span>
          </button>
        )}
      </div>

      {/* Memory items */}
      {memoryItems.length === 0 && !memoryLoading ? (
        <div className="panel-empty">
          <Brain size={28} className="panel-empty-icon" />
          <p>No memory summaries yet.</p>
          <p className="text-[10px]" style={{ color: "var(--muted-2)" }}>
            They appear automatically after every 10 messages
          </p>
        </div>
      ) : (
        <div className="memory-list">
          {memoryItems.map((item, i) => (
            <motion.div
              key={i}
              className="memory-chip"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05, duration: 0.2 }}
            >
              <div className="memory-chip-header">
                <Brain size={12} className="memory-chip-icon" />
                <span className="text-[10px] font-semibold" style={{ color: "var(--accent-2)" }}>
                  Memory
                </span>
                <span className="memory-chip-score">
                  {item.score < 1 ? `${(item.score * 100).toFixed(0)}% match` : "Summary"}
                </span>
              </div>
              <p className="memory-chip-content">{item.content}</p>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
