"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { CommandPalette } from "@/components/layout/CommandPalette";
import { BottomChat } from "@/components/chat/BottomChat";
import { ToastContainer } from "@/components/ui/toast";
import { useStudioStore } from "@/store/useStudioStore";

export function ShellLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
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
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.15, ease: "easeOut" }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
        <BottomChat />
      </div>
      <CommandPalette />
      <ToastContainer />
    </div>
  );
}
