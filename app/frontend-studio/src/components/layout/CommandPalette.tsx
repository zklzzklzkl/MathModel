"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Home,
  FolderOpen,
  Play,
  Settings,
  ShieldCheck,
  FileText,
  Library,
  BarChart3,
  Boxes,
  GraduationCap,
  FlaskConical as Beaker,
} from "lucide-react";
import { useStudioStore, domains } from "@/store/useStudioStore";

interface Command {
  id: string;
  label: string;
  icon: React.ReactNode;
  shortcut?: string;
  action: () => void;
  category: string;
}

const domainIcons: Record<string, React.ReactNode> = {
  math_modeling: <Beaker className="h-4 w-4" />,
  statistics: <BarChart3 className="h-4 w-4" />,
  data_analysis: <Boxes className="h-4 w-4" />,
  paper_writing: <FileText className="h-4 w-4" />,
  homework: <GraduationCap className="h-4 w-4" />,
  research: <Library className="h-4 w-4" />,
};

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const setSelectedDomain = useStudioStore((s) => s.setSelectedDomain);
  const project = useStudioStore((s) => s.project);
  const driver = useStudioStore((s) => s.driver);

  const commands: Command[] = useMemo(
    () => [
      { id: "nav-home", label: "首页", icon: <Home className="h-4 w-4" />, action: () => router.push("/"), category: "导航" },
      { id: "nav-projects", label: "项目管理", icon: <FolderOpen className="h-4 w-4" />, action: () => router.push("/projects"), category: "导航" },
      { id: "nav-runs", label: "运行管理", icon: <Play className="h-4 w-4" />, shortcut: "⌘R", action: () => router.push("/runs"), category: "导航" },
      { id: "nav-templates", label: "模板库", icon: <FileText className="h-4 w-4" />, action: () => router.push("/templates"), category: "导航" },
      { id: "nav-models", label: "模型设置", icon: <Settings className="h-4 w-4" />, action: () => router.push("/models"), category: "导航" },
      { id: "nav-quality", label: "质量检查", icon: <ShieldCheck className="h-4 w-4" />, action: () => router.push("/quality"), category: "导航" },
      ...domains.map((d) => ({
        id: `domain-${d.id}`,
        label: `切换领域: ${d.label}`,
        icon: domainIcons[d.id] ?? <Beaker className="h-4 w-4" />,
        action: () => setSelectedDomain(d.id),
        category: "领域",
      })),
    ],
    [router, setSelectedDomain],
  );

  const filtered = query
    ? commands.filter(
        (c) =>
          c.label.toLowerCase().includes(query.toLowerCase()) ||
          c.category.toLowerCase().includes(query.toLowerCase()),
      )
    : commands;

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    if (open) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((i) => Math.min(i + 1, filtered.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((i) => Math.max(i - 1, 0));
      } else if (e.key === "Enter" && filtered[selectedIndex]) {
        filtered[selectedIndex].action();
        setOpen(false);
      }
    },
    [filtered, selectedIndex],
  );

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.1 }}
        >
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setOpen(false)}
          />
          <motion.div
            className="relative w-full max-w-lg overflow-hidden rounded-xl border border-line bg-white shadow-2xl"
            initial={{ scale: 0.95, y: -10 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.95, y: -10 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
          >
            <div className="flex items-center gap-3 border-b border-line px-4 py-3">
              <Search className="h-4 w-4 text-muted" />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setSelectedIndex(0);
                }}
                onKeyDown={handleKeyDown}
                placeholder="搜索命令..."
                className="flex-1 bg-transparent text-sm text-ink placeholder:text-muted/50 focus:outline-none"
              />
              <kbd className="rounded border border-line bg-panel px-1.5 py-0.5 font-mono text-[10px] text-muted">
                ESC
              </kbd>
            </div>

            <div className="max-h-64 overflow-y-auto py-1">
              {filtered.length === 0 ? (
                <div className="px-4 py-6 text-center text-xs text-muted">未找到匹配的命令</div>
              ) : (
                filtered.map((cmd, idx) => (
                  <button
                    key={cmd.id}
                    onClick={() => {
                      cmd.action();
                      setOpen(false);
                    }}
                    onMouseEnter={() => setSelectedIndex(idx)}
                    className={`flex w-full items-center gap-3 px-4 py-2 text-left text-sm transition-colors ${
                      idx === selectedIndex
                        ? "bg-accent/10 text-accent"
                        : "text-ink hover:bg-panel"
                    }`}
                  >
                    <span className="text-muted">{cmd.icon}</span>
                    <span className="flex-1">{cmd.label}</span>
                    {cmd.shortcut && (
                      <kbd className="rounded border border-line bg-panel px-1.5 py-0.5 font-mono text-[10px] text-muted">
                        {cmd.shortcut}
                      </kbd>
                    )}
                  </button>
                ))
              )}
            </div>

            <div className="flex items-center gap-4 border-t border-line px-4 py-2">
              <span className="text-[10px] text-muted">↑↓ 导航</span>
              <span className="text-[10px] text-muted">↵ 执行</span>
              <span className="text-[10px] text-muted">ESC 关闭</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
