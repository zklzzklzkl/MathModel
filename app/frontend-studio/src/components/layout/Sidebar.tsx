"use client";

import { ChevronRight, Rocket, Search } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useStudioStore, navItems } from "@/store/useStudioStore";

export function Sidebar() {
  const activeNav = useStudioStore((s) => s.activeNav);
  const setActiveNav = useStudioStore((s) => s.setActiveNav);
  const developerMode = useStudioStore((s) => s.developerMode);
  const setDeveloperMode = useStudioStore((s) => s.setDeveloperMode);
  const project = useStudioStore((s) => s.project);

  const navRoutes: Record<string, string> = {
    "首页": "/",
    "项目": "/projects",
    "运行": "/runs",
    "结果": "/runs",
    "模板库": "/templates",
    "模型设置": "/models",
    "质量检查": "/quality",
  };

  return (
    <aside className="border-r border-line bg-white px-5 py-5 max-lg:border-b max-lg:border-r-0">
      <Link href="/" className="mb-6 flex items-center gap-3 no-underline">
        <div className="grid size-10 place-items-center rounded-md bg-accent text-white">
          <Rocket size={22} />
        </div>
        <div>
          <h1 className="text-lg font-semibold text-ink">MathModel Studio</h1>
          <p className="text-xs text-muted">V3 本地私人化工作台</p>
        </div>
      </Link>

      {/* Quick search trigger */}
      <button
        className="mb-3 flex w-full items-center gap-2 rounded-md border border-line px-3 py-2 text-left text-sm text-muted transition-colors hover:border-ink/40 hover:text-ink"
        onClick={() => window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true, bubbles: true }))}
      >
        <Search size={15} />
        <span className="flex-1">搜索命令...</span>
        <kbd className="rounded border border-line bg-panel px-1.5 py-0.5 font-mono text-[10px]">Ctrl+K</kbd>
      </button>

      {/* Navigation with animated pill */}
      <nav className="relative grid gap-1">
        {navItems.map((item) => {
          const isActive = activeNav === item;
          return (
            <Link
              key={item}
              href={navRoutes[item] ?? "/"}
              className={`relative flex h-10 items-center justify-between rounded-md px-3 text-left text-sm no-underline transition-colors ${
                isActive ? "text-white" : "text-muted hover:bg-panel hover:text-ink"
              }`}
              onClick={() => setActiveNav(item)}
            >
              {isActive && (
                <motion.span
                  layoutId="nav-active-pill"
                  className="absolute inset-0 rounded-md bg-ink"
                  transition={{ type: "spring", duration: 0.25 }}
                />
              )}
              <span className="relative z-10">{item}</span>
              {isActive ? <ChevronRight size={16} className="relative z-10" /> : null}
            </Link>
          );
        })}
      </nav>

      {project ? (
        <div className="mt-4 border-t border-line pt-4">
          <p className="text-xs text-muted">活跃项目</p>
          <p className="text-sm font-medium text-ink truncate">{project.name}</p>
        </div>
      ) : null}

      <div className="mt-4 border-t border-line pt-5">
        <label className="flex items-center justify-between text-sm font-medium cursor-pointer">
          开发者模式
          <input
            className="size-4"
            type="checkbox"
            checked={developerMode}
            onChange={(event) => setDeveloperMode(event.target.checked)}
          />
        </label>
      </div>
    </aside>
  );
}
