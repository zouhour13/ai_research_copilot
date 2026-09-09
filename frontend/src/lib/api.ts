import { Session, Message, Source } from "@/types/chat";
import { AgentStep } from "@/types/agent";
import { MemoryItem } from "@/types/memory";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

function errorDetail(error: unknown, fallback: string): string {
  return typeof error === "object" && error !== null && "detail" in error && typeof error.detail === "string"
    ? error.detail
    : fallback;
}

// ─── Sessions ──────────────────────────────────────────────────────────────────

export async function createSession(mode: "chat" | "research" = "chat"): Promise<Session> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function getSessions(): Promise<Session[]> {
  const res = await fetch(`${API_BASE}/sessions`);
  if (!res.ok) throw new Error("Failed to fetch sessions");
  return res.json();
}

export async function getSession(id: number): Promise<Session> {
  const res = await fetch(`${API_BASE}/sessions/${id}`);
  if (!res.ok) throw new Error("Session not found");
  return res.json();
}

export async function renameSession(id: number, title: string): Promise<Session> {
  const res = await fetch(`${API_BASE}/sessions/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Failed to rename session");
  return res.json();
}

export async function deleteSession(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/sessions/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete session");
}

/**
 * P0-6 FIX: Sync the research mode toggle to the backend session.
 */
export async function updateSessionMode(
  id: number,
  mode: "chat" | "research" | "file" | "hybrid"
): Promise<Session> {
  const res = await fetch(`${API_BASE}/sessions/${id}/mode`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
  if (!res.ok) throw new Error("Failed to update session mode");
  return res.json();
}

// ─── Chat ──────────────────────────────────────────────────────────────────────

export async function sendMessageStream(
  sessionId: number,
  content: string,
  mode: "chat" | "research" | "file" | "hybrid",
  onChunk: (chunk: string) => void,
  onSources: (sources: Source[]) => void,
  onTitle: (title: string) => void,
  onAgentStep: (step: AgentStep) => void
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat/${sessionId}/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, mode }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(errorDetail(err, "Failed to send message"));
  }
  if (!res.body) return;

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let eventBuffer = "";

  const handleEvent = (eventBlock: string): boolean => {
    const dataStr = eventBlock
      .split("\n")
      .filter((line) => line.startsWith("data: "))
      .map((line) => line.slice(6))
      .join("\n")
      .trim();

    if (dataStr === "[DONE]") return true;
    if (!dataStr) return false;

    try {
      const data = JSON.parse(dataStr);
      if (data.chunk) onChunk(data.chunk);
      if (data.sources) onSources(data.sources);
      if (data.session_title) onTitle(data.session_title);
      if (data.agent_step) onAgentStep(data.agent_step as AgentStep);
    } catch {
      // A malformed server event should not terminate the entire stream.
    }
    return false;
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    eventBuffer += decoder.decode(value, { stream: true });

    // SSE events are delimited by a blank line, not by a network read.  Keep
    // incomplete data in the buffer so a large sources payload is never lost.
    const completeEvents = eventBuffer.split("\n\n");
    eventBuffer = completeEvents.pop() ?? "";
    for (const eventBlock of completeEvents) {
      if (handleEvent(eventBlock)) return;
    }
  }

  eventBuffer += decoder.decode();
  if (eventBuffer && handleEvent(eventBuffer)) return;
}

export async function getChatHistory(sessionId: number): Promise<Message[]> {
  const res = await fetch(`${API_BASE}/chat/${sessionId}/history`);
  if (!res.ok) throw new Error("Failed to fetch history");
  return res.json();
}

export async function clearMessages(sessionId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/chat/${sessionId}/messages`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to clear messages");
}

export async function exportSession(
  sessionId: number,
  format: "pdf" | "docx"
): Promise<Blob> {
  const res = await fetch(`${API_BASE}/export/${sessionId}?format=${format}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(errorDetail(err, `Export failed (${res.status})`));
  }
  return res.blob();
}

// ─── Documents ─────────────────────────────────────────────────────────────────

export async function uploadDocument(
  sessionId: number,
  file: File
): Promise<{ filename: string; chunks: number; file_url?: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/documents/upload/${sessionId}`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(errorDetail(err, "Failed to upload document"));
  }
  return res.json();
}

// ─── Memory ────────────────────────────────────────────────────────────────────

export async function getMemory(
  sessionId: number,
  query = ""
): Promise<{ memories: MemoryItem[]; count: number }> {
  const url = query
    ? `${API_BASE}/memory/${sessionId}?query=${encodeURIComponent(query)}`
    : `${API_BASE}/memory/${sessionId}`;
  const res = await fetch(url);
  if (!res.ok) return { memories: [], count: 0 };
  return res.json();
}

export async function resetMemory(sessionId: number): Promise<void> {
  await fetch(`${API_BASE}/memory/${sessionId}`, { method: "DELETE" });
}

// ─── Settings ──────────────────────────────────────────────────────────────────

export async function getModels(): Promise<{
  providers: string[];
  defaults: Record<string, string>;
}> {
  const res = await fetch(`${API_BASE}/settings/models`);
  if (!res.ok) throw new Error("Failed to fetch models");
  return res.json();
}

export async function getProviderStatus(): Promise<{
  provider_status: Record<string, boolean>;
  active_provider: string;
  active_model: string;
}> {
  const res = await fetch(`${API_BASE}/settings/status`);
  if (!res.ok) throw new Error("Failed to fetch provider status");
  return res.json();
}

export async function setModel(provider: string, model: string): Promise<void> {
  const res = await fetch(`${API_BASE}/settings/model`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, model }),
  });
  if (!res.ok) throw new Error("Failed to switch model");
}
