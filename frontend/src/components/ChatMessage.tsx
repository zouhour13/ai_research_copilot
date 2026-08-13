"use client";

import { Message } from "@/types/chat";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Copy, Check, Cpu, User, RefreshCw } from "lucide-react";
import { useState } from "react";
import SourceCard from "./SourceCard";
import ThinkingDots from "./ThinkingDots";

interface Props {
  message: Message;
  index: number;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button
      onClick={copy}
      className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-[11px] font-medium transition-all"
      style={{
        background: "var(--surface-hover)",
        color: copied ? "var(--done-color)" : "var(--muted)",
        border: "1px solid var(--border)",
      }}
      title={copied ? "Copied!" : "Copy response"}
    >
      {copied ? <Check size={11} className="text-green-400" /> : <Copy size={11} />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

export default function ChatMessage({ message, index }: Props) {
  const isUser = message.role === "user";

  if (isUser) {
    // ── User message — right-aligned, clean pill style ───────────────
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: Math.min(index * 0.02, 0.1) }}
        className="flex justify-end px-1"
      >
        <div className="flex items-end gap-2.5 max-w-[80%]">
          <div
            className="relative px-4 py-3 rounded-2xl rounded-br-md text-sm leading-relaxed text-white"
            style={{
              background: "linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%)",
              boxShadow: "0 2px 16px rgba(99,102,241,0.25)",
            }}
          >
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
          <div
            className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center mb-0.5 msg-avatar-user"
            style={{ boxShadow: "0 2px 8px rgba(99,102,241,0.3)" }}
          >
            <User size={13} className="text-white" />
          </div>
        </div>
      </motion.div>
    );
  }

  // ── AI message — full-width flowing layout ───────────────────────
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: Math.min(index * 0.02, 0.1) }}
      className="flex gap-3 px-1"
    >
      {/* Avatar */}
      <div
        className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-0.5 msg-avatar-ai"
        style={{ boxShadow: "0 2px 12px rgba(99,102,241,0.35)" }}
      >
        <Cpu size={14} className="text-white" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 flex flex-col gap-3">
        {/* Message body */}
        <div className="text-sm leading-relaxed">
          {message.isLoading ? (
            <ThinkingDots />
          ) : (
            <div className="prose-dark">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Code blocks
                  code({ className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || "");
                    const isBlock = match !== null;
                    if (isBlock) {
                      return (
                        <div className="relative my-3 rounded-xl overflow-hidden"
                          style={{ border: "1px solid var(--border)", background: "#0a0c14" }}
                        >
                          <div
                            className="flex items-center justify-between px-4 py-2.5"
                            style={{ borderBottom: "1px solid var(--border)", background: "#0d0f18" }}
                          >
                            <span className="text-[10.5px] text-muted font-mono font-medium uppercase tracking-wider">
                              {match[1]}
                            </span>
                            <CopyButton text={String(children).replace(/\n$/, "")} />
                          </div>
                          <SyntaxHighlighter
                            style={oneDark}
                            language={match[1]}
                            PreTag="div"
                            customStyle={{
                              margin: 0,
                              background: "#0a0c14",
                              fontSize: "0.8rem",
                              padding: "1.1rem",
                              lineHeight: "1.65",
                            }}
                          >
                            {String(children).replace(/\n$/, "")}
                          </SyntaxHighlighter>
                        </div>
                      );
                    }
                    return (
                      <code
                        className="px-1.5 py-0.5 rounded-md font-mono text-[0.8em]"
                        style={{
                          background: "var(--surface-2)",
                          color: "#a5f3fc",
                          border: "1px solid var(--border)",
                        }}
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  },
                  h1: ({ children }) => (
                    <h1 className="text-lg font-bold mt-5 mb-2 first:mt-0 tracking-tight"
                      style={{ color: "var(--foreground)" }}>
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-base font-semibold mt-4 mb-2 first:mt-0"
                      style={{ color: "var(--foreground)" }}>
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-sm font-semibold mt-3 mb-1.5 first:mt-0"
                      style={{ color: "var(--foreground-dim)" }}>
                      {children}
                    </h3>
                  ),
                  p: ({ children }) => (
                    <p className="mb-3.5 last:mb-0 leading-relaxed"
                      style={{ color: "var(--foreground-dim)" }}>
                      {children}
                    </p>
                  ),
                  ul: ({ children }) => (
                    <ul className="mb-3.5 space-y-1.5 list-disc list-outside pl-5"
                      style={{ color: "var(--foreground-dim)" }}>
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="mb-3.5 space-y-1.5 list-decimal list-outside pl-5"
                      style={{ color: "var(--foreground-dim)" }}>
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => (
                    <li className="leading-relaxed pl-0.5">{children}</li>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote
                      className="pl-4 my-3 italic"
                      style={{
                        borderLeft: "3px solid var(--accent)",
                        color: "var(--muted)",
                      }}
                    >
                      {children}
                    </blockquote>
                  ),
                  table: ({ children }) => (
                    <div
                      className="overflow-x-auto my-4 rounded-xl"
                      style={{ border: "1px solid var(--border)" }}
                    >
                      <table className="w-full text-sm">{children}</table>
                    </div>
                  ),
                  thead: ({ children }) => (
                    <thead style={{ background: "var(--surface-2)" }}>{children}</thead>
                  ),
                  th: ({ children }) => (
                    <th
                      className="px-4 py-2.5 text-left text-xs font-semibold"
                      style={{
                        color: "var(--muted)",
                        borderBottom: "1px solid var(--border)",
                      }}
                    >
                      {children}
                    </th>
                  ),
                  td: ({ children }) => (
                    <td
                      className="px-4 py-2.5"
                      style={{
                        color: "var(--foreground-dim)",
                        borderBottom: "1px solid rgba(30,35,51,0.5)",
                      }}
                    >
                      {children}
                    </td>
                  ),
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="transition-colors"
                      style={{
                        color: "var(--accent)",
                        textDecoration: "underline",
                        textUnderlineOffset: "3px",
                        textDecorationColor: "var(--accent-glow)",
                      }}
                    >
                      {children}
                    </a>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-semibold" style={{ color: "var(--foreground)" }}>
                      {children}
                    </strong>
                  ),
                  hr: () => (
                    <hr className="my-4" style={{ borderColor: "var(--border)" }} />
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Sources */}
        {!isUser &&
          !message.isLoading &&
          message.sources &&
          message.sources.length > 0 && (
            <SourceCard sources={message.sources} />
          )}

        {/* Footer: timestamp + copy */}
        {!message.isLoading && (
          <div className="flex items-center gap-3">
            {message.created_at && (
              <span className="text-[10.5px]" style={{ color: "var(--muted-2)" }}>
                {new Date(message.created_at).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            )}
            <CopyButton text={message.content} />
          </div>
        )}
      </div>
    </motion.div>
  );
}
