"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { ToastContainer } from "@/components/ui/toast";
import { useStudioStore } from "@/store/useStudioStore";

export function ShellLayout({ children }: { children: ReactNode }) {
  const refreshStudioData = useStudioStore((s) => s.refreshStudioData);

  useEffect(() => {
    void refreshStudioData();
  }, [refreshStudioData]);

  return (
    <div className="grid min-h-screen grid-cols-[260px_1fr] max-lg:grid-cols-1">
      <Sidebar />
      <div className="flex flex-col min-h-screen max-lg:min-h-0">
        <Header />
        <main className="flex-1 studio-scroll overflow-auto px-6 py-5">
          {children}
        </main>
      </div>
      <ToastContainer />
    </div>
  );
}
