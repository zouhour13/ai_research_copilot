export interface Source {
  title: string;
  url: string;
  excerpt?: string;
  source_type?: "web" | "document";
}

export interface Message {
  id?: number;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  created_at?: string;
  isLoading?: boolean;
}

export interface Session {
  id: number;
  mode: "chat" | "research" | "file" | "hybrid";
  title: string;
  file_name?: string | null;
  file_url?: string | null;
  file_search_store_name?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  session_title: string;
}