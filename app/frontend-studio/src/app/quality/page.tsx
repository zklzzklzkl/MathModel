"use client";

import { AlertTriangle, Check, FileX, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { useStudioStore, qualityItems } from "@/store/useStudioStore";
import { apiFetch } from "@/lib/api";

type QualityItem = {
  id: string;
  path: string;
  status: "missing" | "present" | "pass" | "fail";
  preview: string;
};

type DevDiagnostics = {
  mathmodel_root: string;
  workspace_root: string;
  db_path: string;
  template_root: string;
  python: string;
  langgraph?: { available: boolean; error: string | null; supported_modes: string[] };
  prompt_templates: string[];
};

export default function QualityPage() {
  const project = useStudioStore((s) => s.project);
  const developerMode = useStudioStore((s) => s.developerMode);
  const [qualityData, setQualityData] = useState<QualityItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [devData, setDevData] = useState<DevDiagnostics | null>(null);

  useEffect(() => {
    if (project?.id) {
      setBusy(true);
      apiFetch<{ items: QualityItem[] }>(`/api/projects/${project.id}/quality`)
        .then((data) => setQualityData(data.items))
        .catch(() => setQualityData([]))
        .finally(() => setBusy(false));
    }
  }, [project?.id]);

  useEffect(() => {
    if (developerMode) {
      apiFetch<DevDiagnostics>("/api/dev/diagnostics")
        .then((data) => setDevData(data))
        .catch(() => setDevData(null));
    }
  }, [developerMode]);

  const statusIcon = (status: string) => {
    if (status === "pass") return <Check size={16} className="text-accent" />;
    if (status === "fail") return <AlertTriangle size={16} className="text-amber" />;
    if (status === "present") return <Check size={16} className="text-muted" />;
    return <FileX size={16} className="text-muted" />;
  };

  const statusLabel = (status: string) => {
    if (status === "pass") return "通过";
    if (status === "fail") return "需关注";
    if (status === "present") return "已存在";
    return "缺失";
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-ink">质量检查</h2>
      <div className="rounded-md border border-line bg-white p-4 shadow-soft">
        <div className="mb-3 flex items-center gap-2">
          <ShieldCheck size={18} />
          <h3 className="font-semibold">V2 竞赛质量内核</h3>
        </div>
        {!project ? (
          <p className="text-sm text-muted">请先在首页创建项目并完成一次运行，质量报告将在此展示</p>
        ) : busy ? (
          <p className="text-sm text-muted">加载中...</p>
        ) : (
          <div className="grid gap-2">
            {qualityData.length > 0
              ? qualityData.map((item) => (
                  <details key={item.id} className="rounded-md border border-line">
                    <summary className="flex cursor-pointer items-center justify-between px-3 py-2">
                      <div className="flex items-center gap-2">
                        {statusIcon(item.status)}
                        <span className="text-sm font-medium">{qualityItems.find((q) => q[0] === item.id)?.[1] ?? item.id}</span>
                      </div>
                      <span className="text-xs text-muted">{statusLabel(item.status)}</span>
                    </summary>
                    {item.preview ? (
                      <pre className="max-h-40 overflow-auto border-t border-line bg-panel px-3 py-2 text-xs whitespace-pre-wrap">
                        {item.preview}
                      </pre>
                    ) : (
                      <p className="border-t border-line px-3 py-2 text-xs text-muted">暂无内容</p>
                    )}
                  </details>
                ))
              : qualityItems.map(([id, label]) => (
                  <div
                    key={id}
                    className="flex items-center justify-between rounded-md border border-line px-3 py-2"
                  >
                    <span className="text-sm">{label}</span>
                    <span className="text-xs text-muted">{id}</span>
                  </div>
                ))}
          </div>
        )}
      </div>

      {developerMode ? (
        <div className="rounded-md border border-line bg-white p-4 shadow-soft">
          <div className="mb-3 flex items-center gap-2">
            <ShieldCheck size={18} />
            <h3 className="font-semibold">开发者模式</h3>
          </div>
          {devData ? (
            <div className="space-y-3 text-sm">
              <div>
                <p className="font-medium text-ink">LangGraph 状态</p>
                <p className="text-muted">
                  {devData.langgraph?.available ? (
                    <span className="text-accent">已安装 · {devData.langgraph.supported_modes.length} 个可用 mode</span>
                  ) : (
                    <span className="text-amber">未安装 · {devData.langgraph?.error ?? "未知"}</span>
                  )}
                </p>
                {devData.langgraph?.available ? (
                  <p className="mt-1 text-xs text-muted">
                    Modes: {devData.langgraph.supported_modes.join(", ")}
                  </p>
                ) : null}
              </div>
              <div>
                <p className="font-medium text-ink">Prompt 模板</p>
                <p className="text-xs text-muted">
                  {devData.prompt_templates.length > 0
                    ? devData.prompt_templates.join(", ")
                    : "未找到模板文件"}
                </p>
              </div>
              <div>
                <p className="font-medium text-ink">路径信息</p>
                <p className="text-xs text-muted">DB: {devData.db_path}</p>
                <p className="text-xs text-muted">Workspace: {devData.workspace_root}</p>
                <p className="text-xs text-muted">Templates: {devData.template_root}</p>
              </div>
            </div>
          ) : (
            <div className="grid gap-2 text-sm">
              <span>LangGraph 原始配置</span>
              <span>Prompt / Harness</span>
              <span>Raw Artifacts</span>
              <span>Benchmark Lab</span>
              <span>调试日志</span>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
