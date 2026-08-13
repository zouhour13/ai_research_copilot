"use client";

import { useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowDown } from "lucide-react";
import { useAppStore } from "@/lib/store";
import ChatMessage from "./ChatMessage";
import EmptyState from "./EmptyState";
import { useState } from "react";

export default function ChatWindow() {
  const { messages } = useAppStore();
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [showScrollBtn, setShowScrollBtn] = useState(false);

  const scrollToBottom = (smooth = true) => {
    bottomRef.current?.scrollIntoView({
      behavior: smooth ? "smooth" : "instant",
    });
  };

  // Auto-scroll when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Track scroll position to show/hide scroll button
  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    const distFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    setShowScrollBtn(distFromBottom > 200);
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="relative flex-1 overflow-hidden">
      {/* Fade gradient at top for depth */}
      {hasMessages && (
        <div
          className="absolute top-0 left-0 right-0 h-12 z-10 pointer-events-none"
          style={{
            background: "linear-gradient(to bottom, var(--bg) 0%, transparent 100%)",
          }}
        />
      )}

      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="h-full overflow-y-auto px-4 py-8"
      >
        {!hasMessages ? (
          <EmptyState />
        ) : (
          <div className="max-w-3xl mx-auto flex flex-col gap-7 pb-4">
            <AnimatePresence initial={false}>
              {messages.map((msg, i) => (
                <ChatMessage key={msg.id ?? i} message={msg} index={i} />
              ))}
            </AnimatePresence>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Scroll to bottom button */}
      <AnimatePresence>
        {showScrollBtn && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 8 }}
            transition={{ duration: 0.15 }}
            onClick={() => scrollToBottom()}
            className="absolute bottom-5 right-5 p-2.5 rounded-full z-10 transition-all"
            style={{
              background: "var(--surface-2)",
              border: "1px solid var(--border-2)",
              color: "var(--muted)",
              boxShadow: "0 4px 20px rgba(0,0,0,0.5)",
            }}
          >
            <ArrowDown size={15} />
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  );
}
