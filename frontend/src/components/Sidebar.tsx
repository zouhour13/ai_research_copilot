"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState, useRef, useEffect } from "react";
import {
  Plus,
  Search,
  Trash2,
  Pencil,
  Check,
  X,
  MessageSquare,
  Globe,
  ChevronLeft,
  Cpu,
  Eraser,
  Download,
  FileText,
  Sparkles,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import ModelSelector from "@/components/ui/ModelSelector";
import { toast } from "sonner";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function downloadExport(sessionId: number, format: "pdf" | "docx", filename: string) {
  try {
    const res = await fetch(`${API_BASE}/export/${sessionId}?format=${format}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error((err as any).detail || `Export failed (${res.status})`);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success(`${format.toUpperCase()} exported successfully`);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Export failed";
    toast.error(msg);
  }
}

function timeAgo(dateStr?: string): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const now = new Date();
  const diff = (now.getTime() - date.getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function getDateGroup(dateStr?: string): string {
  if (!dateStr) return "Older";
  const date = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / 86400000);
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return "This Week";
  if (diffDays < 30) return "This Month";
  return "Older";
}

export default function Sidebar() {
  const {
    sessions,
    activeSessionId,
    selectSession,
    createNewSession,
    deleteSession,
    clearHistory,
    renameSession,
    toggleSidebar,
  } = useAppStore();

  const [search, setSearch] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const editRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editingId !== null) editRef.current?.focus();
  }, [editingId]);

  const filtered = sessions.filter((s) =>
    (s.title ?? "").toLowerCase().includes(search.toLowerCase())
  );

  // Group sessions by date
  const grouped: Record<string, typeof sessions> = {};
  filtered.forEach((s) => {
    const group = getDateGroup(s.updated_at);
    if (!grouped[group]) grouped[group] = [];
    grouped[group].push(s);
  });
  const groupOrder = ["Today", "Yesterday", "This Week", "This Month", "Older"];

  const handleRename = async (id: number) => {
    const trimmed = editTitle.trim();
    if (trimmed) await renameSession(id, trimmed);
    setEditingId(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent, id: number) => {
    if (e.key === "Enter") handleRename(id);
    if (e.key === "Escape") setEditingId(null);
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Collapse button */}
      <button
        onClick={toggleSidebar}
        className="absolute top-4 right-[-13px] z-50 w-6 h-6 flex items-center justify-center rounded-full bg-surface-2 border border-border text-muted hover:text-foreground hover:border-border-2 transition-all shadow-md"
        aria-label="Close sidebar"
      >
        <ChevronLeft size={11} />
      </button>

      <div className="flex flex-col h-full overflow-hidden">
        {/* ── Header ─────────────────────────────────────────── */}
        <div className="p-4 border-b border-border flex-shrink-0">
          {/* Brand */}
          <div className="flex items-center gap-3 mb-4">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent to-accent-2 flex items-center justify-center shadow-glow flex-shrink-0">
              <Cpu size={17} className="text-white" />
            </div>
            <div>
              <p className="font-bold text-sm text-foreground leading-none tracking-tight gradient-text">
                Nexus Research
              </p>
              <p className="text-[10.5px] text-muted mt-0.5 flex items-center gap-1">
                <Sparkles size={9} className="text-accent/60" />
                AI-powered copilot
              </p>
            </div>
          </div>

          {/* New Chat button */}
          <button
            id="new-chat-btn"
            onClick={createNewSession}
            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-sm font-semibold text-white transition-all active:scale-95"
            style={{
              background: "linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%)",
              boxShadow: "0 2px 16px rgba(99,102,241,0.4), 0 0 0 1px rgba(99,102,241,0.15)",
            }}
          >
            <Plus size={15} />
            New Chat
          </button>
        </div>

        {/* ── Search ──────────────────────────────────────────── */}
        <div className="px-3 py-2.5 flex-shrink-0">
          <div className="relative">
            <Search
              size={12}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none"
            />
            <input
              type="text"
              placeholder="Search conversations…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-2 text-xs bg-surface border border-border rounded-lg text-foreground placeholder:text-muted-2 focus:outline-none focus:ring-1 focus:ring-accent/40 focus:border-accent/40 transition-all"
            />
          </div>
        </div>

        {/* ── Session list ─────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto px-2 pb-4 scrollbar-thin">
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center gap-2">
              <MessageSquare size={24} className="text-muted/30" />
              <p className="text-xs text-muted">
                {search ? "No results found" : "No conversations yet"}
              </p>
              {!search && (
                <p className="text-[10px] text-muted/50">
                  Start a new chat to get going
                </p>
              )}
            </div>
          ) : (
            <div className="space-y-1">
              {groupOrder.map((group) => {
                const items = grouped[group];
                if (!items || items.length === 0) return null;
                return (
                  <div key={group}>
                    <p className="sidebar-section-label mt-3 first:mt-1">{group}</p>
                    <ul className="space-y-0.5">
                      {items.map((s) => (
                        <motion.li
                          key={s.id}
                          layout
                          initial={{ opacity: 0, x: -8 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: -8 }}
                          transition={{ duration: 0.15 }}
                        >
                          <div
                            onClick={() => editingId !== s.id && selectSession(s.id)}
                            className={`group relative flex items-center gap-2 px-2.5 py-2 rounded-xl cursor-pointer transition-all ${
                              activeSessionId === s.id
                                ? "bg-accent/12 text-foreground border border-accent/20"
                                : "text-muted hover:bg-surface-hover hover:text-foreground border border-transparent"
                            }`}
                          >
                            {/* Active indicator bar */}
                            {activeSessionId === s.id && (
                              <span className="absolute left-0 top-1/4 bottom-1/4 w-0.5 rounded-full bg-accent" />
                            )}

                            {/* Mode icon */}
                            <div className="flex-shrink-0 ml-0.5">
                              {s.mode === "research" ? (
                                <Globe size={12} className={activeSessionId === s.id ? "text-accent" : ""} />
                              ) : (
                                <MessageSquare size={12} className={activeSessionId === s.id ? "text-accent" : ""} />
                              )}
                            </div>

                            {/* Document badge */}
                            {s.file_name && (
                              <div
                                className="flex-shrink-0 text-teal/70"
                                title={`Document: ${s.file_name}`}
                              >
                                <FileText size={11} />
                              </div>
                            )}

                            {/* Title / edit input */}
                            <div className="flex-1 min-w-0">
                              {editingId === s.id ? (
                                <input
                                  ref={editRef}
                                  value={editTitle}
                                  onChange={(e) => setEditTitle(e.target.value)}
                                  onKeyDown={(e) => handleKeyDown(e, s.id)}
                                  onClick={(e) => e.stopPropagation()}
                                  className="w-full text-xs bg-surface border border-accent/40 rounded-md px-1.5 py-0.5 text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                                />
                              ) : (
                                <>
                                  <p className="text-xs font-medium truncate leading-snug">
                                    {s.title || "New Chat"}
                                  </p>
                                  <p className="text-[10px] text-muted/50 mt-0.5">
                                    {timeAgo(s.updated_at)}
                                  </p>
                                </>
                              )}
                            </div>

                            {/* Action buttons */}
                            <div
                              className={`flex items-center gap-0.5 transition-opacity flex-shrink-0 ${
                                editingId === s.id || confirmDeleteId === s.id
                                  ? "opacity-100"
                                  : "opacity-0 group-hover:opacity-100"
                              }`}
                              onClick={(e) => e.stopPropagation()}
                            >
                              {editingId === s.id ? (
                                <>
                                  <button
                                    onClick={() => handleRename(s.id)}
                                    className="p-1 rounded hover:text-green-400 transition-colors"
                                    title="Save"
                                  >
                                    <Check size={11} />
                                  </button>
                                  <button
                                    onClick={() => setEditingId(null)}
                                    className="p-1 rounded hover:text-red-400 transition-colors"
                                    title="Cancel"
                                  >
                                    <X size={11} />
                                  </button>
                                </>
                              ) : confirmDeleteId === s.id ? (
                                <div className="flex items-center gap-1 bg-red-950/60 border border-red-500/30 rounded-lg px-2 py-0.5">
                                  <span className="text-[10px] text-red-400">Delete?</span>
                                  <button
                                    onClick={() => {
                                      deleteSession(s.id);
                                      setConfirmDeleteId(null);
                                    }}
                                    className="p-0.5 rounded hover:text-red-300 text-red-400 transition-colors"
                                    title="Confirm delete"
                                  >
                                    <Check size={11} />
                                  </button>
                                  <button
                                    onClick={() => setConfirmDeleteId(null)}
                                    className="p-0.5 rounded hover:text-foreground text-muted transition-colors"
                                    title="Cancel"
                                  >
                                    <X size={11} />
                                  </button>
                                </div>
                              ) : (
                                <>
                                  <button
                                    onClick={() => {
                                      setEditingId(s.id);
                                      setEditTitle(s.title ?? "");
                                    }}
                                    className="p-1 rounded hover:text-foreground transition-colors"
                                    title="Rename"
                                  >
                                    <Pencil size={11} />
                                  </button>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      const fname = `${(s.title ?? "report").replace(/\s+/g, "_")}.pdf`;
                                      downloadExport(s.id, "pdf", fname);
                                    }}
                                    className="p-1 rounded hover:text-blue-400 transition-colors"
                                    title="Export PDF"
                                  >
                                    <Download size={11} />
                                  </button>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      const fname = `${(s.title ?? "report").replace(/\s+/g, "_")}.docx`;
                                      downloadExport(s.id, "docx", fname);
                                    }}
                                    className="p-1 rounded hover:text-indigo-400 transition-colors"
                                    title="Export DOCX"
                                  >
                                    <FileText size={11} />
                                  </button>
                                  <button
                                    onClick={() => clearHistory(s.id)}
                                    className="p-1 rounded hover:text-yellow-400 transition-colors"
                                    title="Clear chat history"
                                  >
                                    <Eraser size={11} />
                                  </button>
                                  <button
                                    onClick={() => setConfirmDeleteId(s.id)}
                                    className="p-1 rounded hover:text-red-400 transition-colors"
                                    title="Delete conversation"
                                  >
                                    <Trash2 size={11} />
                                  </button>
                                </>
                              )}
                            </div>
                          </div>
                        </motion.li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* ── Footer ──────────────────────────────────────────── */}
        <div className="p-3 border-t border-border space-y-2 flex-shrink-0">
          {/* Model selector */}
          <ModelSelector />

          {/* User row */}
          <div className="flex items-center gap-2.5 px-2 py-2 rounded-xl hover:bg-surface-hover cursor-pointer transition-all group">
            <div className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold text-white flex-shrink-0 shadow-md"
              style={{ background: "linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)" }}
            >
              U
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-foreground leading-none">User</p>
              <p className="text-[10px] text-muted mt-0.5">Free Plan</p>
            </div>
            <div className="w-1.5 h-1.5 rounded-full bg-done flex-shrink-0" style={{ boxShadow: "0 0 4px var(--done-color)" }} />
          </div>
        </div>
      </div>
    </div>
  );
}
