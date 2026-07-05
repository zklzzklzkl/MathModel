"use client";

import { Search } from "lucide-react";
import { useStudioStore } from "@/store/useStudioStore";

export function Header() {
  const currentDomain = useStudioStore((s) => s.currentDomain);
  const message = useStudioStore((s) => s.message);
  const run = useStudioStore((s) => s.run);

  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-line bg-white px-6 py-3">
      <div>
        <p className="text-sm text-muted">{currentDomain().label}</p>
        <h2 className="text-xl font-semibold text-ink">本地 AI 建模与科研 Studio</h2>
      </div>
      <div className="flex items-center gap-3">
        {/* Search bar trigger */}
        <button
          className="hidden sm:flex items-center gap-2 rounded-md border border-line bg-panel px-3 py-1.5 text-sm text-muted transition-colors hover:border-ink/40 hover:text-ink"
          onClick={() =>
            window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true, bubbles: true }))
          }
        >
          <Search size={14} />
          <span>搜索...</span>
          <kbd className="ml-2 rounded border border-line bg-white px-1.5 py-0.5 font-mono text-[10px]">Ctrl+K</kbd>
        </button>
        {run ? (
          <span
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              run.status === "running"
                ? "bg-[#eef9f6] text-accent"
                : run.status === "paused"
                  ? "bg-[#fff7ed] text-amber"
                  : "bg-panel text-muted"
            }`}
          >
            {run.status} · {run.current_stage}
          </span>
        ) : null}
        <div className="flex items-center gap-2 rounded-md border border-line bg-panel px-3 py-2 text-sm">
          <span className="text-muted">状态</span>
          <strong className="text-ink">{message}</strong>
        </div>
      </div>
    </header>
  );
}
