"use client";

import { motion } from "framer-motion";

export default function ThinkingDots() {
  return (
    <div className="flex items-center gap-2 py-1 px-1">
      <div className="flex items-center gap-1.5">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="rounded-full"
            style={{ width: 7, height: 7, background: "var(--accent)" }}
            animate={{
              scale: [0.8, 1.3, 0.8],
              opacity: [0.35, 1, 0.35],
            }}
            transition={{
              duration: 1.2,
              repeat: Infinity,
              delay: i * 0.22,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>
      <span
        className="text-xs font-medium animate-pulse"
        style={{ color: "var(--muted)" }}
      >
        Thinking…
      </span>
    </div>
  );
}
