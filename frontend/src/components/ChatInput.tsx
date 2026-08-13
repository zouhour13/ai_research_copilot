"use client";

import { useRef, useState, useEffect, KeyboardEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Globe,
  MessageSquare,
  Square,
  FileText,
  CheckCircle2,
  AlertCircle,
  Paperclip,
  ExternalLink,
} from "lucide-react";
import { useAppStore } from "@/lib/store";

const PLACEHOLDER_CYCLES = [
  "Ask anything…",
  "Research a topic with web sources…",
  "Debug your code…",
  "Explain a concept…",
  "Summarize an article…",
];

export default function ChatInput() {
  const {
    sendMessage,
    isLoading,
    isResearchMode,
    toggleResearchMode,
    isUploading,
    uploadFile,
    sessions,
    activeSessionId,
  } = useAppStore();

  const [input, setInput] = useState("");
  const [placeholder, setPlaceholder] = useState(PLACEHOLDER_CYCLES[0]);
  const [isTogglingMode, setIsTogglingMode] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const phIndex = useRef(0);

  // Derive document state from active session
  const activeSession = sessions.find((s) => s.id === activeSessionId) ?? null;
  const uploadedFile = activeSession?.file_name ?? null;
  const hasDocument = !!activeSession?.file_search_store_name;

  const handleToggleMode = async () => {
    setIsTogglingMode(true);
    try {
      await (toggleResearchMode as () => Promise<void>)();
    } finally {
      setIsTogglingMode(false);
    }
  };

  // Cycle placeholder text when empty
  useEffect(() => {
    if (input) return;
    const interval = setInterval(() => {
      phIndex.current = (phIndex.current + 1) % PLACEHOLDER_CYCLES.length;
      setPlaceholder(PLACEHOLDER_CYCLES[phIndex.current]);
    }, 3500);
    return () => clearInterval(interval);
  }, [input]);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
  }, [input]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isLoading) return;
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    await sendMessage(text);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const canSend = input.trim().length > 0 && !isLoading;

  const containerClass = isResearchMode
    ? "input-glass research-mode"
    : hasDocument
    ? "input-glass doc-mode"
    : "input-glass";

  return (
    <div className="px-4 pb-5 pt-2">
      <div className="max-w-3xl mx-auto">
        {/* ── Document status bar ──────────────────────────────────── */}
        <AnimatePresence>
          {isUploading && (
            <motion.div
              key="uploading"
              initial={{ opacity: 0, y: 4, height: 0 }}
              animate={{ opacity: 1, y: 0, height: "auto" }}
              exit={{ opacity: 0, y: 4, height: 0 }}
              className="overflow-hidden"
            >
              <div
                className="flex items-center gap-2 mb-2 px-3.5 py-2.5 rounded-xl text-[11px] font-medium"
                style={{
                  background: "rgba(99,102,241,0.08)",
                  border: "1px solid rgba(99,102,241,0.2)",
                  color: "var(--accent)",
                }}
              >
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                  </svg>
                </motion.div>
                Processing document…
              </div>
            </motion.div>
          )}

          {!isUploading && hasDocument && uploadedFile && (
            <motion.div
              key="document-ready"
              initial={{ opacity: 0, y: 4, height: 0 }}
              animate={{ opacity: 1, y: 0, height: "auto" }}
              exit={{ opacity: 0, y: 4, height: 0 }}
              className="overflow-hidden"
            >
              <div
                className="flex items-center gap-2 mb-2 px-3.5 py-2.5 rounded-xl text-[11px]"
                style={{
                  background: "rgba(20,184,166,0.07)",
                  border: "1px solid rgba(20,184,166,0.2)",
                }}
              >
                <CheckCircle2 size={12} className="text-emerald-400 flex-shrink-0" />
                <FileText size={11} className="text-emerald-400/70 flex-shrink-0" />
                {activeSession?.file_url ? (
                  <a
                    href={activeSession.file_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-medium truncate max-w-[260px] hover:underline cursor-pointer transition-colors"
                    style={{ color: "#34d399" }}
                    title={`Click to open ${uploadedFile}`}
                  >
                    {uploadedFile}
                  </a>
                ) : (
                  <span
                    className="font-medium truncate max-w-[260px]"
                    style={{ color: "#34d399" }}
                    title={uploadedFile}
                  >
                    {uploadedFile}
                  </span>
                )}
                {activeSession?.file_url && (
                  <a
                    href={activeSession.file_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 ml-1 p-0.5 rounded hover:bg-emerald-400/10 transition-colors"
                    title={`Open / download ${uploadedFile}`}
                    aria-label="Open document"
                  >
                    <ExternalLink size={10} style={{ color: "rgba(52,211,153,0.7)" }} />
                  </a>
                )}
                <span className="ml-auto flex-shrink-0" style={{ color: "rgba(52,211,153,0.5)" }}>
                  RAG active
                </span>
              </div>
            </motion.div>
          )}

          {!isUploading && !hasDocument && activeSession?.file_name && (
            <motion.div
              key="document-processing"
              initial={{ opacity: 0, y: 4, height: 0 }}
              animate={{ opacity: 1, y: 0, height: "auto" }}
              exit={{ opacity: 0, y: 4, height: 0 }}
              className="overflow-hidden"
            >
              <div
                className="flex items-center gap-2 mb-2 px-3.5 py-2.5 rounded-xl text-[11px]"
                style={{
                  background: "rgba(251,191,36,0.07)",
                  border: "1px solid rgba(251,191,36,0.2)",
                  color: "#fbbf24",
                }}
              >
                <AlertCircle size={12} className="flex-shrink-0" />
                <span>{activeSession.file_name} — saved (non-PDF, not indexed for RAG)</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Research/Hybrid mode label ────────────────────────────── */}
        <AnimatePresence>
          {isResearchMode && (
            <motion.div
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 4 }}
              className="flex items-center gap-1.5 mb-2 px-1"
            >
              <div
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10.5px] font-semibold"
                style={{
                  background: "var(--accent-dim)",
                  border: "1px solid var(--accent-glow)",
                  color: "var(--accent)",
                }}
              >
                <Globe size={10} />
                {hasDocument ? "Hybrid Mode — Document RAG + Web Research" : "Research Mode — Web-sourced answers with citations"}
                {hasDocument && <FileText size={10} className="text-emerald-400" />}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Input box ────────────────────────────────────────────── */}
        <div className={containerClass}>
          <textarea
            ref={textareaRef}
            id="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              hasDocument
                ? `Ask about "${uploadedFile}"…`
                : placeholder
            }
            rows={1}
            disabled={isLoading}
            className="w-full resize-none bg-transparent px-4 pt-3.5 pb-2 text-sm text-foreground placeholder:text-muted focus:outline-none disabled:opacity-50 leading-relaxed"
            style={{ minHeight: "52px", maxHeight: "200px", fontFamily: "var(--font-sans)" }}
          />

          <div className="flex items-center justify-between px-3 pb-3 pt-0 gap-2">
            {/* Left: mode toggle */}
            <motion.button
              id="research-mode-toggle"
              onClick={handleToggleMode}
              disabled={isTogglingMode}
              whileTap={{ scale: 0.95 }}
              title={isResearchMode ? "Switch to Chat mode" : "Switch to Research mode"}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all disabled:opacity-60 ${
                isResearchMode ? "mode-toggle-active" : "mode-toggle-idle"
              }`}
            >
              <AnimatePresence mode="wait">
                {isResearchMode ? (
                  <motion.span
                    key="globe"
                    initial={{ scale: 0.7, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.7, opacity: 0 }}
                    transition={{ duration: 0.12 }}
                  >
                    <Globe size={12} />
                  </motion.span>
                ) : (
                  <motion.span
                    key="msg"
                    initial={{ scale: 0.7, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.7, opacity: 0 }}
                    transition={{ duration: 0.12 }}
                  >
                    <MessageSquare size={12} />
                  </motion.span>
                )}
              </AnimatePresence>
              {isResearchMode ? (hasDocument ? "Hybrid" : "Research") : "Chat"}
            </motion.button>

            {/* Right: file + send */}
            <div className="flex items-center gap-1.5">
              <input
                type="file"
                id="file-upload"
                className="hidden"
                accept=".pdf,.csv,.xlsx,.xls"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) uploadFile(file);
                  e.target.value = "";
                }}
              />

              {/* Upload button */}
              <motion.button
                onClick={() => document.getElementById("file-upload")?.click()}
                disabled={isUploading}
                whileTap={{ scale: 0.9 }}
                className="flex items-center justify-center w-8 h-8 rounded-xl transition-all"
                style={{
                  background: isUploading
                    ? "var(--surface-hover)"
                    : hasDocument
                    ? "rgba(20,184,166,0.1)"
                    : "transparent",
                  color: isUploading
                    ? "var(--muted)"
                    : hasDocument
                    ? "#34d399"
                    : "var(--muted)",
                  border: hasDocument ? "1px solid rgba(20,184,166,0.2)" : "1px solid transparent",
                }}
                title={
                  isUploading
                    ? "Processing document…"
                    : hasDocument
                    ? `Document: ${uploadedFile} (click to replace)`
                    : "Upload PDF or CSV"
                }
              >
                {isUploading ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                    </svg>
                  </motion.div>
                ) : hasDocument ? (
                  <FileText size={14} />
                ) : (
                  <Paperclip size={14} />
                )}
              </motion.button>

              {/* Hint */}
              <p className="text-[10px] hidden sm:block ml-1 mr-0.5" style={{ color: "var(--muted-2)" }}>
                ⏎ to send
              </p>

              {/* Send button */}
              <motion.button
                id="send-btn"
                onClick={handleSend}
                disabled={!canSend && !isLoading}
                whileTap={canSend ? { scale: 0.9 } : {}}
                whileHover={canSend ? { scale: 1.05 } : {}}
                className="flex items-center justify-center w-8 h-8 rounded-xl transition-all"
                style={{
                  background: canSend
                    ? "linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%)"
                    : isLoading
                    ? "var(--surface-hover)"
                    : "var(--surface-hover)",
                  color: canSend ? "white" : "var(--muted)",
                  boxShadow: canSend ? "0 2px 12px rgba(99,102,241,0.4)" : "none",
                  cursor: canSend || isLoading ? "pointer" : "not-allowed",
                }}
                title="Send (Enter)"
              >
                {isLoading ? (
                  <Square size={11} className="animate-pulse" style={{ color: "var(--muted)" }} />
                ) : (
                  <Send size={13} />
                )}
              </motion.button>
            </div>
          </div>
        </div>

        {/* Disclaimer */}
        <p className="text-center text-[10px] mt-2.5" style={{ color: "var(--muted-2)" }}>
          Nexus Research may make mistakes · Verify important information
        </p>
      </div>
    </div>
  );
}
