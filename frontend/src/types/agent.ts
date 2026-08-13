export interface AgentStep {
  message: string;
  step_type: "search" | "retrieve" | "think" | "cite" | "done" | "error";
  detail?: string;
}

export interface AgentTrace {
  steps: AgentStep[];
  status: "idle" | "thinking" | "searching" | "retrieving" | "done" | "error";
}
