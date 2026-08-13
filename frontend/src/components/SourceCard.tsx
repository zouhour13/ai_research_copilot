"use client";

import { Source } from "@/types/chat";
import { ExternalLink, FileText } from "lucide-react";
import { motion } from "framer-motion";

interface Props {
  sources: Source[];
}

function getDomain(url: string): string {
  try {
    return new URL(url).hostname.replace("www.", "");
  } catch {
    return url;
  }
}

function getFavicon(url: string): string | null {
  try {
    if (!url) return null;
    const { protocol, hostname } = new URL(url);
    if (!hostname) return null;
    return `https://www.google.com/s2/favicons?domain=${protocol}//${hostname}&sz=16`;
  } catch {
    return null;
  }
}

function isDocumentSource(source: Source): boolean {
  return source.source_type === "document" || source.url?.startsWith("page:");
}

export default function SourceCard({ sources }: Props) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="flex flex-col gap-2">
      <p
        className="text-[10.5px] font-semibold uppercase tracking-widest"
        style={{ color: "var(--muted-2)" }}
      >
        {sources.length} Source{sources.length !== 1 ? "s" : ""}
      </p>
      <div className="flex flex-wrap gap-1.5">
        {sources.map((source, i) => {
          const isDoc = isDocumentSource(source);
          const displayTitle = source.title
            ? source.title.length > 35
              ? source.title.slice(0, 35) + "…"
              : source.title
            : getDomain(source.url);
          const faviconUrl = getFavicon(source.url);

          if (isDoc) {
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.92 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.05, duration: 0.2 }}
                className="source-pill"
                title={source.excerpt || source.title}
              >
                <FileText size={10} style={{ color: "var(--accent)", flexShrink: 0 }} />
                <span className="truncate" style={{ color: "var(--foreground-dim)" }}>
                  {displayTitle}
                </span>
              </motion.div>
            );
          }

          return (
            <motion.a
              key={i}
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              initial={{ opacity: 0, scale: 0.92 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05, duration: 0.2 }}
              className="source-pill group"
              title={source.excerpt || source.title}
            >
              {faviconUrl && (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img
                  src={faviconUrl}
                  alt=""
                  width={12}
                  height={12}
                  className="flex-shrink-0 opacity-80 group-hover:opacity-100 rounded-sm"
                  onError={(e) => (e.currentTarget.style.display = "none")}
                />
              )}
              <span className="truncate">{displayTitle}</span>
              <ExternalLink
                size={9}
                className="flex-shrink-0 opacity-0 group-hover:opacity-50 transition-opacity"
              />
            </motion.a>
          );
        })}
      </div>
    </div>
  );
}
