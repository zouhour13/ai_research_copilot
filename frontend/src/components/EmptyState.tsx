"use client";

import { motion } from "framer-motion";
import {
  Globe,
  FileText,
  BookOpen,
  GitCompare,
  Brain,
  Download,
  Sparkles,
  Zap,
} from "lucide-react";
import { useAppStore } from "@/lib/store";

const SUGGESTIONS = [
  {
    icon: Globe,
    label: "Research a topic",
    prompt: "Research the latest advances in quantum computing and summarize key findings",
    mode: "research" as const,
    color: "from-blue-500/20 to-accent/10",
    iconColor: "text-blue-400",
    border: "hover:border-blue-500/30",
  },
  {
    icon: FileText,
    label: "Analyze a document",
    prompt: "Upload a PDF and I'll extract key insights, findings, and citations",
    mode: "chat" as const,
    color: "from-teal/20 to-emerald-500/10",
    iconColor: "text-teal-400",
    border: "hover:border-teal-500/30",
  },
  {
    icon: BookOpen,
    label: "Summarize research",
    prompt: "What are the key differences between RAG and fine-tuning for LLMs?",
    mode: "research" as const,
    color: "from-violet-500/20 to-accent-2/10",
    iconColor: "text-violet-400",
    border: "hover:border-violet-500/30",
  },
  {
    icon: GitCompare,
    label: "Compare findings",
    prompt: "Compare transformer and state-space models for sequence modeling",
    mode: "research" as const,
    color: "from-orange-500/20 to-yellow-500/10",
    iconColor: "text-orange-400",
    border: "hover:border-orange-500/30",
  },
  {
    icon: Brain,
    label: "Explain a concept",
    prompt: "Explain how vector embeddings work and why they are useful for semantic search",
    mode: "chat" as const,
    color: "from-pink-500/20 to-rose-500/10",
    iconColor: "text-pink-400",
    border: "hover:border-pink-500/30",
  },
  {
    icon: Download,
    label: "Export research",
    prompt: "Summarize everything we've discussed so I can export it as a report",
    mode: "chat" as const,
    color: "from-accent/20 to-accent-2/10",
    iconColor: "text-accent",
    border: "hover:border-accent/30",
  },
];

const CAPABILITIES = [
  { label: "Upload PDFs", icon: FileText },
  { label: "Web Research", icon: Globe },
  { label: "Export Reports", icon: Download },
  { label: "AI Memory", icon: Brain },
];

export default function EmptyState() {
  const { sendMessage, createNewSession, activeSessionId } = useAppStore();

  const handleSuggestion = async (prompt: string) => {
    if (!activeSessionId) {
      await createNewSession();
    }
    await sendMessage(prompt);
  };

  return (
    <div className="flex flex-col items-center justify-center h-full px-6 py-8 text-center select-none">
      {/* Hero logo */}
      <motion.div
        initial={{ scale: 0.6, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 180, damping: 18, delay: 0.05 }}
        className="relative mb-6"
      >
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center"
          style={{
            background: "linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%)",
            boxShadow: "0 0 40px rgba(99,102,241,0.4), 0 4px 24px rgba(99,102,241,0.3), 0 0 0 1px rgba(99,102,241,0.2)",
          }}
        >
          <Sparkles size={28} className="text-white" />
        </div>
        {/* Glow ring */}
        <div
          className="absolute inset-0 rounded-2xl"
          style={{
            background: "linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%)",
            filter: "blur(20px)",
            opacity: 0.25,
            zIndex: -1,
          }}
        />
      </motion.div>

      {/* Title + subtitle */}
      <motion.div
        initial={{ y: 12, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.12, duration: 0.35 }}
        className="mb-2"
      >
        <h1 className="text-2xl font-bold tracking-tight mb-2 gradient-text">
          Nexus Research
        </h1>
        <p className="text-sm max-w-xs leading-relaxed" style={{ color: "var(--muted)" }}>
          Your AI-powered research workspace.
          <br />
          Ask questions, explore topics, and get{" "}
          <span style={{ color: "var(--accent)" }} className="font-medium">
            web-sourced answers
          </span>{" "}
          with citations.
        </p>
      </motion.div>

      {/* Capability badges */}
      <motion.div
        initial={{ y: 10, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.3 }}
        className="flex flex-wrap items-center justify-center gap-2 mb-7"
      >
        {CAPABILITIES.map((cap, i) => (
          <div
            key={i}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-medium"
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              color: "var(--muted)",
            }}
          >
            <cap.icon size={11} style={{ color: "var(--accent)" }} />
            {cap.label}
          </div>
        ))}
      </motion.div>

      {/* Suggestion cards */}
      <motion.div
        initial={{ y: 16, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.24, duration: 0.35 }}
        className="w-full max-w-2xl grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5"
      >
        {SUGGESTIONS.map((s, i) => (
          <motion.button
            key={i}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.28 + i * 0.045, duration: 0.3 }}
            whileHover={{ y: -3, transition: { duration: 0.15 } }}
            whileTap={{ scale: 0.97 }}
            onClick={() => handleSuggestion(s.prompt)}
            className={`suggestion-card ${s.border} group`}
            id={`suggestion-${i}`}
          >
            {/* Gradient top accent */}
            <div
              className={`absolute top-0 left-0 right-0 h-px rounded-t-xl bg-gradient-to-r ${s.color} opacity-60`}
            />

            <div className="flex items-start gap-3 relative">
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-transform group-hover:scale-110"
                style={{
                  background: `linear-gradient(135deg, ${s.color.includes("blue") ? "rgba(59,130,246,0.15)" : s.color.includes("teal") ? "rgba(20,184,166,0.15)" : s.color.includes("violet") ? "rgba(139,92,246,0.15)" : s.color.includes("orange") ? "rgba(251,146,60,0.15)" : s.color.includes("pink") ? "rgba(236,72,153,0.15)" : "rgba(99,102,241,0.15)"} 0%, transparent 100%)`,
                }}
              >
                <s.icon size={15} className={s.iconColor} />
              </div>
              <div className="text-left flex-1 min-w-0">
                <p className="text-xs font-semibold mb-1 flex items-center gap-1.5"
                  style={{ color: "var(--foreground)" }}>
                  {s.label}
                  {s.mode === "research" && (
                    <span
                      className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full"
                      style={{
                        background: "var(--accent-dim)",
                        color: "var(--accent)",
                        border: "1px solid var(--accent-glow)",
                      }}
                    >
                      web
                    </span>
                  )}
                </p>
                <p className="text-[11px] leading-relaxed line-clamp-2"
                  style={{ color: "var(--muted)" }}>
                  {s.prompt}
                </p>
              </div>
            </div>
          </motion.button>
        ))}
      </motion.div>

      {/* Footer hint */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7, duration: 0.4 }}
        className="mt-7 flex items-center gap-2 flex-wrap justify-center"
      >
        {["Upload a PDF to chat with documents", "Enable Research Mode for web sources", "Export sessions as PDF or DOCX"].map((hint, i) => (
          <>
            {i > 0 && (
              <span key={`sep-${i}`} className="w-1 h-1 rounded-full" style={{ background: "var(--muted-2)" }} />
            )}
            <span key={hint} className="text-[10.5px]" style={{ color: "var(--muted-2)" }}>
              {hint}
            </span>
          </>
        ))}
      </motion.div>
    </div>
  );
}
