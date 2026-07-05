"use client";

import { ChevronRight, Rocket } from "lucide-react";
import Link from "next/link";
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
      {/* Brand */}
      <Link href="/" className="mb-6 flex items-center gap-3 no-underline">
        <div className="grid size-10 place-items-center rounded-md bg-accent text-white">
          <Rocket size={22} />
        </div>
        <div>
          <h1 className="text-lg font-semibold text-ink">MathModel Studio</h1>
          <p className="text-xs text-muted">V3 本地私人化工作台</p>
        </div>
      </Link>

      {/* Navigation */}
      <nav className="grid gap-1">
        {navItems.map((item) => (
          <Link
            key={item}
            href={navRoutes[item] ?? "/"}
            className={`flex h-10 items-center justify-between rounded-md px-3 text-left text-sm no-underline ${
              activeNav === item ? "bg-ink text-white" : "text-muted hover:bg-panel hover:text-ink"
            }`}
            onClick={() => setActiveNav(item)}
          >
            {item}
            {activeNav === item ? <ChevronRight size={16} /> : null}
          </Link>
        ))}
      </nav>

      {/* Project indicator */}
      {project ? (
        <div className="mt-4 border-t border-line pt-4">
          <p className="text-xs text-muted">活跃项目</p>
          <p className="text-sm font-medium text-ink truncate">{project.name}</p>
        </div>
      ) : null}

      {/* Developer mode toggle */}
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
