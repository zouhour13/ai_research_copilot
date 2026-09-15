"use client";

import { ExternalLink, Globe, FileText, BookOpen } from "lucide-react";
import { motion } from "framer-motion";

interface Source {
  title: string;
  url: string;
  excerpt?: string;
  source_type?: string;
  domain?: string;
  published_date?: string;
  retrieved_at?: string;
  rank?: number;
  quality_score?: number;
}

interface SourcePanelProps {
  sources: Source[];
  label?: string;
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
    if (!url || url.startsWith("page:")) return null;
    const { protocol, hostname } = new URL(url);
    return `https://www.google.com/s2/favicons?domain=${protocol}//${hostname}&sz=16`;
  } catch {
    return null;
  }
}

export default function SourcePanel({ sources, label }: SourcePanelProps) {
  if (!sources || sources.length === 0) {
    return (
      <div className="panel-empty">
        <BookOpen size={30} className="panel-empty-icon" />
        <p>Sources from the latest response will appear here.</p>
        <p className="text-[10px]" style={{ color: "var(--muted-2)" }}>
          Enable Research Mode and ask a question
        </p>
      </div>
    );
  }

  return (
    <div className="source-panel">
      <p className="source-count">
        {label ? `${label} - ` : ""}
        {sources.length} source{sources.length !== 1 ? "s" : ""}
      </p>
      <div className="source-list">
        {sources.map((source, i) => {
          const isDoc = source.source_type === "document" || source.url?.startsWith("page:");
          const faviconUrl = !isDoc ? getFavicon(source.url) : null;
          const domain = !isDoc ? (source.domain || getDomain(source.url)) : null;
          const quality = typeof source.quality_score === "number"
            ? Math.round(source.quality_score * 100)
            : null;

          return (
            <motion.div
              key={i}
              className="source-card"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06, duration: 0.2 }}
            >
              <div className="source-card-header">
                <span className="source-num">[{i + 1}]</span>

                {/* Icon: favicon or type icon */}
                <span className="source-type-icon flex-shrink-0">
                  {isDoc ? (
                    <FileText size={12} style={{ color: "var(--accent)" }} />
                  ) : faviconUrl ? (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img
                      src={faviconUrl}
                      alt=""
                      width={13}
                      height={13}
                      className="rounded-sm opacity-80"
                      onError={(e) => {
                        e.currentTarget.style.display = "none";
                      }}
                    />
                  ) : (
                    <Globe size={12} />
                  )}
                </span>

                <a
                  href={source.url?.startsWith("page:") ? "#" : source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="source-title"
                  title={source.title}
                >
                  {source.title}
                </a>

                {!source.url?.startsWith("page:") && (
                  <ExternalLink size={11} className="source-ext-icon" />
                )}
              </div>

              {/* Domain */}
              {domain && (
                <p className="text-[10px] mt-1.5" style={{ color: "var(--muted-2)" }}>
                  {domain}
                </p>
              )}

              {!isDoc && (
                <div className="source-meta-row">
                  {source.rank ? <span>Rank {source.rank}</span> : null}
                  {quality !== null ? <span>Quality {quality}%</span> : null}
                  {source.published_date ? <span>{source.published_date}</span> : null}
                </div>
              )}

              {/* Excerpt */}
              {source.excerpt && (
                <p className="source-excerpt">{source.excerpt}</p>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
