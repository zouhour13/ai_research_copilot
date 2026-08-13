"use client";

import { useEffect, useRef, useState } from "react";
import { Cpu, ChevronDown, Check } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAppStore } from "@/lib/store";
import { getModels } from "@/lib/api";

const MODEL_OPTIONS: Record<string, string[]> = {
  gemini: ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
  openai: ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
  claude: ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
  local: ["llama3.2", "mistral", "phi3"],
};

const PROVIDER_ICONS: Record<string, string> = {
  gemini: "✦",
  openai: "⊕",
  claude: "◈",
  local: "⊞",
};

export default function ModelSelector({ placement = "sidebar" }: { placement?: "sidebar" | "topbar" }) {
  const { currentProvider, currentModel, setModel } = useAppStore();
  const [isOpen, setIsOpen] = useState(false);
  const [providers, setProviders] = useState<string[]>(["gemini", "openai", "claude", "local"]);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getModels()
      .then((data) => setProviders(data.providers))
      .catch(() => {});
  }, []);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;
    const handle = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, [isOpen]);

  const shortModel = currentModel.split("-").slice(0, 3).join("-");

  return (
    <div className={`model-selector model-selector-${placement}`} ref={dropdownRef}>
      <button
        className="model-selector-btn"
        onClick={() => setIsOpen((v) => !v)}
        title="Switch LLM model"
        aria-label="Model selector"
        id="model-selector-btn"
      >
        <Cpu size={13} style={{ color: "var(--accent)" }} />
        <span className="model-selector-label capitalize">
          {currentProvider}
          <span className="opacity-50 mx-1">/</span>
          <span className="opacity-70">{shortModel}</span>
        </span>
        <ChevronDown
          size={11}
          className={`chevron ${isOpen ? "chevron-open" : ""}`}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="model-dropdown"
            initial={{ opacity: 0, y: 4, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.97 }}
            transition={{ duration: 0.14 }}
          >
            {providers.map((provider) => (
              <div key={provider} className="model-provider-group">
                <p className="model-provider-label flex items-center gap-1.5">
                  <span className="text-[12px] opacity-60">
                    {PROVIDER_ICONS[provider] ?? "◉"}
                  </span>
                  {provider}
                </p>
                {(MODEL_OPTIONS[provider] ?? []).map((model) => {
                  const active = currentProvider === provider && currentModel === model;
                  return (
                    <button
                      key={model}
                      className={`model-option ${active ? "model-option-active" : ""}`}
                      onClick={() => {
                        setModel(provider, model);
                        setIsOpen(false);
                      }}
                    >
                      <span className="flex-1">{model}</span>
                      {active && <Check size={12} className="model-check" />}
                    </button>
                  );
                })}
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
