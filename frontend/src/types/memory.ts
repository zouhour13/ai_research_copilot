export interface MemoryItem {
  content: string;
  metadata: Record<string, unknown>;
  score: number;
}

export type MemoryTier = "working" | "episodic" | "semantic";

export interface MemoryState {
  items: MemoryItem[];
  count: number;
  isLoading: boolean;
}
