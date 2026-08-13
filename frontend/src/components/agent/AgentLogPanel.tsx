"use client";

import { motion } from "framer-motion";
import { Search, FileText, Brain, CheckCircle, AlertCircle, Clock } from "lucide-react";
import { useAppStore } from "@/lib/store";

const ICON_MAP: Record<string, React.ReactNode> = {
  search: <Search size={12} />,
  retrieve: <FileText size={12} />,
  think: <Brain size={12} />,
  cite: <CheckCircle size={12} />,
  done: <CheckCircle size={12} />,
  error: <AlertCircle size={12} />,
};

const COLOR_MAP: Record<string, string> = {
  search: "log-search",
  retrieve: "log-retrieve",
  think: "log-think",
  cite: "log-cite",
  done: "log-done",
  error: "log-error",
};

const DOT_COLORS: Record<string, string> = {
  search: "var(--search-color)",
  retrieve: "var(--retrieve-color)",
  think: "var(--think-color)",
  cite: "var(--done-color)",
  done: "var(--done-color)",
  error: "var(--error-color)",
};

export default function AgentLogPanel() {
  const { agentTrace, agentStatus } = useAppStore();

  if (agentTrace.length === 0) {
    return (
      <div className="panel-empty">
        <Clock size={30} className="panel-empty-icon" />
        <p>Agent steps will appear here during a response.</p>
        <p className="text-[10px]" style={{ color: "var(--muted-2)" }}>
          Try sending a message in Research Mode
        </p>
      </div>
    );
  }

  return (
    <div className="agent-log">
      {/* Status header */}
      <div className="agent-log-status flex items-center gap-2">
        <span>Status:</span>
        <span className={`status-badge status-${agentStatus}`}>{agentStatus}</span>
        <span className="ml-auto text-[10px]" style={{ color: "var(--muted-2)" }}>
          {agentTrace.length} step{agentTrace.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Timeline steps */}
      <div className="relative pl-4" style={{ borderLeft: "1px solid var(--border)" }}>
        {agentTrace.map((step, i) => (
          <motion.div
            key={i}
            className={`relative mb-1 last:mb-0`}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.04, duration: 0.18 }}
          >
            {/* Timeline dot */}
            <div
              className="absolute -left-[21px] top-2.5 w-2.5 h-2.5 rounded-full border-2 flex-shrink-0"
              style={{
                borderColor: DOT_COLORS[step.step_type] ?? "var(--border-2)",
                background: DOT_COLORS[step.step_type]
                  ? `${DOT_COLORS[step.step_type]}22`
                  : "var(--surface)",
              }}
            />

            {/* Step content */}
            <div
              className={`agent-log-step ${COLOR_MAP[step.step_type] ?? ""}`}
              style={{ borderLeftColor: "transparent", paddingLeft: "12px" }}
            >
              <span className="log-step-icon flex-shrink-0 mt-0.5">
                {ICON_MAP[step.step_type]}
              </span>
              <span className="log-step-msg text-[12px]">{step.message}</span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
