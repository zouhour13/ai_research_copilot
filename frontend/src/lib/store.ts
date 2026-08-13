"use client";

import { create } from "zustand";
import { Session, Message } from "@/types/chat";
import { AgentStep } from "@/types/agent";
import { MemoryItem } from "@/types/memory";
import {
  createSession,
  getSessions,
  getChatHistory,
  sendMessageStream as apiSendMessageStream,
  deleteSession as apiDeleteSession,
  renameSession as apiRenameSession,
  clearMessages as apiClearMessages,
  uploadDocument,
  getMemory,
  setModel as apiSetModel,
  updateSessionMode,
} from "@/lib/api";
import { toast } from "sonner";

interface AppStore {
  // ── Core state ────────────────────────────────────────────────────
  sessions: Session[];
  activeSessionId: number | null;
  messages: Message[];
  isLoading: boolean;
  isSidebarOpen: boolean;
  isResearchMode: boolean;
  isUploading: boolean;

  // ── Agent state ───────────────────────────────────────────────────
  agentTrace: AgentStep[];
  agentStatus: "idle" | "thinking" | "searching" | "retrieving" | "done";
  addAgentStep: (step: AgentStep) => void;
  clearAgentTrace: () => void;

  // ── Memory state ──────────────────────────────────────────────────
  memoryItems: MemoryItem[];
  memoryLoading: boolean;
  loadMemory: (sessionId: number, query?: string) => Promise<void>;

  // ── Model state ───────────────────────────────────────────────────
  currentProvider: string;
  currentModel: string;
  setModel: (provider: string, model: string) => Promise<void>;

  // ── Right panel ───────────────────────────────────────────────────
  isRightPanelOpen: boolean;
  rightPanelTab: "sources" | "memory" | "agent";
  toggleRightPanel: () => void;
  setRightPanelTab: (tab: "sources" | "memory" | "agent") => void;

  // ── Core actions ──────────────────────────────────────────────────
  loadSessions: () => Promise<void>;
  selectSession: (id: number) => Promise<void>;
  createNewSession: () => Promise<void>;
  deleteSession: (id: number) => Promise<void>;
  clearHistory: (id: number) => Promise<void>;
  renameSession: (id: number, title: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  uploadFile: (file: File) => Promise<void>;
  toggleSidebar: () => void;
  toggleResearchMode: () => Promise<void>;
}

export const useAppStore = create<AppStore>((set, get) => ({
  sessions: [],
  activeSessionId: null,
  messages: [],
  isLoading: false,
  isSidebarOpen: true,
  isResearchMode: false,
  isUploading: false,

  // Agent
  agentTrace: [],
  agentStatus: "idle",
  addAgentStep: (step) =>
    set((state) => ({
      agentTrace: [...state.agentTrace, step],
      agentStatus:
        step.step_type === "done"
          ? "done"
          : step.step_type === "search"
          ? "searching"
          : step.step_type === "retrieve"
          ? "retrieving"
          : "thinking",
    })),
  clearAgentTrace: () => set({ agentTrace: [], agentStatus: "idle" }),

  // Memory
  memoryItems: [],
  memoryLoading: false,
  loadMemory: async (sessionId, query = "") => {
    set({ memoryLoading: true });
    try {
      const data = await getMemory(sessionId, query);
      set({ memoryItems: data.memories, memoryLoading: false });
    } catch {
      set({ memoryLoading: false });
    }
  },

  // Model
  currentProvider: "gemini",
  currentModel: "gemini-2.5-flash",
  setModel: async (provider, model) => {
    try {
      await apiSetModel(provider, model);
      set({ currentProvider: provider, currentModel: model });
      toast.success(`Switched to ${provider} / ${model}`);
    } catch {
      toast.error("Failed to switch model");
    }
  },

  // Right panel
  isRightPanelOpen: false,
  rightPanelTab: "sources",
  toggleRightPanel: () =>
    set((state) => ({ isRightPanelOpen: !state.isRightPanelOpen })),
  setRightPanelTab: (tab) => set({ rightPanelTab: tab }),

  // ── Sessions ──────────────────────────────────────────────────────
  loadSessions: async () => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    try {
      const sessions = await getSessions();
      // Attach file_url for sessions that have a file_name (including historical ones)
      const sessionsWithUrl = sessions.map((s) =>
        s.file_name ? { ...s, file_url: s.file_url ?? `${apiBase}/documents/file/${s.id}` } : s
      );
      set({ sessions: sessionsWithUrl });
    } catch {
      toast.error("Could not load conversation history");
    }
  },

  selectSession: async (id) => {
    if (get().activeSessionId === id) return;
    set({ activeSessionId: id, messages: [], isLoading: true });
    get().clearAgentTrace();
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    try {
      const history = await getChatHistory(id);
      // Sync local research mode toggle with the session's stored mode
      const session = get().sessions.find((s) => s.id === id);
      // Ensure file_url is present for sessions with documents (backwards compat)
      if (session?.file_name && !session.file_url) {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === id ? { ...s, file_url: `${apiBase}/documents/file/${id}` } : s
          ),
        }));
      }
      set({
        messages: history,
        isLoading: false,
        isResearchMode: session?.mode === "research",
      });
    } catch {
      toast.error("Could not load conversation");
      set({ isLoading: false });
    }
  },

  createNewSession: async () => {
    const currentMode = get().isResearchMode ? "research" : "chat";
    try {
      // P0-6 FIX: pass mode when creating so backend session matches frontend state
      const session = await createSession(currentMode);
      set((state) => ({
        sessions: [session, ...state.sessions],
        activeSessionId: session.id,
        messages: [],
        agentTrace: [],
        agentStatus: "idle",
      }));
    } catch {
      toast.error("Could not create new chat");
    }
  },

  deleteSession: async (id) => {
    try {
      await apiDeleteSession(id);
      let nextSessionId: number | null = null;
      set((state) => {
        const sessions = state.sessions.filter((s) => s.id !== id);
        nextSessionId =
          state.activeSessionId === id ? (sessions[0]?.id ?? null) : state.activeSessionId;
        return { sessions, activeSessionId: nextSessionId, messages: [] };
      });
      if (nextSessionId) {
        const history = await getChatHistory(nextSessionId);
        set({ messages: history });
      }
      toast.success("Conversation deleted");
    } catch {
      toast.error("Could not delete conversation");
    }
  },

  clearHistory: async (id) => {
    try {
      await apiClearMessages(id);
      set((state) => ({
        messages: state.activeSessionId === id ? [] : state.messages,
        sessions: state.sessions.map((s) =>
          s.id === id ? { ...s, title: "New Chat" } : s
        ),
        agentTrace: [],
        agentStatus: "idle",
        memoryItems: [],
      }));
      toast.success("Chat history cleared");
    } catch {
      toast.error("Could not clear history");
    }
  },

  renameSession: async (id, title) => {
    try {
      const updated = await apiRenameSession(id, title);
      set((state) => ({
        sessions: state.sessions.map((s) => (s.id === id ? updated : s)),
      }));
    } catch {
      toast.error("Could not rename conversation");
    }
  },

  // ── Send message ───────────────────────────────────────────────────
  sendMessage: async (content) => {
    let sessionId = get().activeSessionId;

    if (!sessionId) {
      try {
        const currentMode = get().isResearchMode ? "research" : "chat";
        const session = await createSession(currentMode);
        sessionId = session.id;
        set((state) => ({
          sessions: [session, ...state.sessions],
          activeSessionId: session.id,
        }));
      } catch {
        toast.error("Could not start a conversation");
        return;
      }
    }

    const userMessage: Message = { role: "user", content };
    const loadingMessage: Message = { role: "assistant", content: "", isLoading: true };

    set((state) => ({
      messages: [...state.messages, userMessage, loadingMessage],
      isLoading: true,
      agentTrace: [],
      agentStatus: "thinking",
    }));

    try {
      await apiSendMessageStream(
        sessionId,
        content,
        (chunk) => {
          set((state) => {
            const newMessages = [...state.messages];
            const lastMsg = newMessages[newMessages.length - 1];
            if (lastMsg && lastMsg.role === "assistant") {
              lastMsg.content = (lastMsg.content || "") + chunk;
              lastMsg.isLoading = false;
            }
            return { messages: newMessages };
          });
        },
        (sources) => {
          set((state) => {
            const newMessages = [...state.messages];
            const lastMsg = newMessages[newMessages.length - 1];
            if (lastMsg && lastMsg.role === "assistant") {
              lastMsg.sources = sources;
            }
            return { messages: newMessages, isRightPanelOpen: sources.length > 0 };
          });
        },
        (title) => {
          set((state) => ({
            sessions: state.sessions.map((s) =>
              s.id === sessionId ? { ...s, title: title || s.title } : s
            ),
          }));
        },
        (step) => {
          get().addAgentStep(step);
        }
      );

      set({ isLoading: false, agentStatus: "done" });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Something went wrong";
      set((state) => {
        const newMessages = [...state.messages];
        const lastMsg = newMessages[newMessages.length - 1];
        if (lastMsg && lastMsg.role === "assistant") {
          lastMsg.content = `**Error:** ${msg}`;
          lastMsg.isLoading = false;
        }
        return { messages: newMessages, isLoading: false, agentStatus: "idle" };
      });
      toast.error(msg);
    }
  },

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),

  // P0-6 / P1-4 FIX: sync research mode to the backend session
  toggleResearchMode: async () => {
    const newMode = get().isResearchMode ? "chat" : "research";
    // Optimistically update UI
    set({ isResearchMode: newMode === "research" });

    const sessionId = get().activeSessionId;
    if (sessionId) {
      try {
        const updated = await updateSessionMode(sessionId, newMode);
        // Update session in list to reflect new mode
        set((state) => ({
          sessions: state.sessions.map((s) => (s.id === sessionId ? updated : s)),
        }));
      } catch {
        // Revert on failure
        set({ isResearchMode: newMode !== "research" });
        toast.error("Could not update research mode");
      }
    }
  },

  uploadFile: async (file) => {
    let sessionId = get().activeSessionId;
    if (!sessionId) {
      try {
        const currentMode = get().isResearchMode ? "research" : "chat";
        const session = await createSession(currentMode);
        sessionId = session.id;
        set((state) => ({
          sessions: [session, ...state.sessions],
          activeSessionId: session.id,
        }));
      } catch {
        toast.error("Could not start a session for upload");
        return;
      }
    }

    set({ isUploading: true });
    try {
      const result = await uploadDocument(sessionId, file);
      const isPdf = file.name.toLowerCase().endsWith(".pdf");
      const isCsvXlsx =
        file.name.toLowerCase().endsWith(".csv") ||
        file.name.toLowerCase().endsWith(".xls") ||
        file.name.toLowerCase().endsWith(".xlsx");
      const isIndexed = isPdf || isCsvXlsx;

      toast.success(
        isIndexed
          ? `Document indexed — ${result.chunks} chunks ready`
          : `File saved — ${file.name}`
      );

      // Sync session mode to "file" on backend so orchestrator routes to RAG
      if (isIndexed) {
        try {
          await updateSessionMode(sessionId, "file");
        } catch {
          // Non-fatal — the backend already sets the mode in documents.py
        }
      }

      // Update session to reflect file upload and mode change.
      // Backend sets file_search_store_name + mode="file" for all indexed types.
      // Also store file_url so the UI can open/preview the document.
      const fileUrl = result.file_url ?? `${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/documents/file/${sessionId}`;
      set((state) => ({
        isUploading: false,
        sessions: state.sessions.map((s) =>
          s.id === sessionId
            ? {
                ...s,
                file_name: file.name,
                file_url: fileUrl,
                file_search_store_name: isIndexed
                  ? `session_${sessionId}`
                  : s.file_search_store_name,
                mode: isIndexed ? "file" : s.mode,
              }
            : s
        ),
        messages: [
          ...state.messages,
          {
            role: "assistant" as const,
            content: isPdf
              ? `**Document ready:** \`${file.name}\` has been indexed (${result.chunks} chunks). You can now ask me anything about it — I'll retrieve relevant passages and cite page numbers.`
              : isCsvXlsx
              ? `**Spreadsheet ready:** \`${file.name}\` has been indexed (${result.chunks} chunks). You can now ask me to summarize it, find specific data, or answer questions about its contents.`
              : `**File saved:** \`${file.name}\`. Note: This file type is not indexed for semantic search.`,
          },
        ],
      }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to upload file";
      toast.error(msg);
      set({ isUploading: false });
    }
  },
}));
