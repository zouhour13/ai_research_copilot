import { Session, Message, ChatResponse } from "@/types/chat";
import { AgentStep } from "@/types/agent";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

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
  mode: "chat" | "research"
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
  onChunk: (chunk: string) => void,
  onSources: (sources: any[]) => void,
  onTitle: (title: string) => void,
  onAgentStep: (step: AgentStep) => void
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat/${sessionId}/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as any).detail || "Failed to send message");
  }
  if (!res.body) return;

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunkStr = decoder.decode(value, { stream: true });

    for (const line of chunkStr.split("\n")) {
      if (!line.startsWith("data: ")) continue;
      const dataStr = line.slice(6).trim();
      if (dataStr === "[DONE]") return;
      if (!dataStr) continue;

      try {
        const data = JSON.parse(dataStr);
        if (data.chunk) onChunk(data.chunk);
        if (data.sources) onSources(data.sources);
        if (data.session_title) onTitle(data.session_title);
        if (data.agent_step) onAgentStep(data.agent_step as AgentStep);
      } catch {
        // ignore parse errors on partial chunks
      }
    }
  }
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
    throw new Error((err as any).detail || `Export failed (${res.status})`);
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
    throw new Error((err as any).detail || "Failed to upload document");
  }
  return res.json();
}

// ─── Memory ────────────────────────────────────────────────────────────────────

export async function getMemory(
  sessionId: number,
  query = ""
): Promise<{ memories: any[]; count: number }> {
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
