"use client";

import { useEffect } from "react";
import { useAppStore } from "@/lib/store";
import AppLayout from "@/components/AppLayout";

export default function Home() {
  const { loadSessions } = useAppStore();

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  return <AppLayout />;
}
