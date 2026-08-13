"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  FileText,
  Brain,
  CheckCircle,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { useAppStore } from "@/lib/store";

const STEP_ICONS: Record<string, React.ReactNode> = {
  search: <Search size={12} />,
  retrieve: <FileText size={12} />,
  think: <Brain size={12} />,
  cite: <CheckCircle size={12} />,
  done: <CheckCircle size={12} />,
  error: <AlertCircle size={12} />,
};

const STEP_COLORS: Record<string, string> = {
  search: "var(--search-color)",
  retrieve: "var(--retrieve-color)",
  think: "var(--think-color)",
  cite: "var(--done-color)",
  done: "var(--done-color)",
  error: "var(--error-color)",
};

export default function AgentActivityBar() {
  const { agentTrace, agentStatus, isLoading } = useAppStore();

  if (!isLoading && agentStatus === "idle") return null;

  const latestStep = agentTrace[agentTrace.length - 1];
  const stepColor = latestStep ? STEP_COLORS[latestStep.step_type] : "var(--accent)";

  return (
    <AnimatePresence>
      <motion.div
        className="agent-bar"
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 6 }}
        transition={{ duration: 0.2 }}
      >
        <div
          className="agent-bar-inner rounded-2xl px-4 py-2 inline-flex items-center gap-2.5"
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border-2)",
            boxShadow: "0 2px 16px rgba(0,0,0,0.4)",
          }}
        >
          {/* Spinner */}
          {agentStatus !== "done" && (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
              style={{ color: "var(--accent)" }}
            >
              <Loader2 size={13} />
            </motion.div>
          )}

          {/* Colored step icon */}
          {latestStep && (
            <span style={{ color: stepColor }}>
              {STEP_ICONS[latestStep.step_type]}
            </span>
          )}

          {/* Latest step text */}
          {latestStep && (
            <AnimatePresence mode="wait">
              <motion.span
                key={latestStep.message}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.15 }}
                className="text-[11.5px] font-medium"
                style={{ color: stepColor }}
              >
                {latestStep.message}
              </motion.span>
            </AnimatePresence>
          )}

          {/* Step count badge */}
          {agentTrace.length > 1 && (
            <span
              className="text-[10px] font-semibold px-2 py-0.5 rounded-full ml-0.5"
              style={{
                background: "var(--accent-dim)",
                color: "var(--accent)",
                border: "1px solid var(--accent-glow)",
              }}
            >
              {agentTrace.length} steps
            </span>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
