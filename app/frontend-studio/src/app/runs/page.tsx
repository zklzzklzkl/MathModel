"use client";

import {
  Activity,
  Check,
  Play,
  RefreshCw,
  Square,
} from "lucide-react";
import dynamic from "next/dynamic";
import { useStudioStore, timeline } from "@/store/useStudioStore";
import { apiFetch, type StudioRun } from "@/lib/api";

const WorkflowGraph = dynamic(
  () => import("@/components/workflow-graph").then((m) => ({ default: m.WorkflowGraph })),
  { ssr: false },
);

export default function RunsPage() {
  const store = useStudioStore();
  const currentStage = store.currentStage();
  const gateRequired = store.gate?.status === "required";

  async function handleResume() {
    if (!store.run) return;
    const run = await apiFetch<StudioRun>(`/api/runs/${store.run.id}/resume`, { method: "POST", body: "{}" });
    useStudioStore.getState().setRun(run);
    useStudioStore.getState().refreshRun(run.id);
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-ink">运行管理</h2>

      {!store.run ? (
        <p className="text-sm text-muted">暂无运行，请在首页创建项目并启动运行</p>
      ) : (
        <>
          {/* Timeline */}
          <div className="rounded-md border border-line bg-white p-4 shadow-soft">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="font-semibold">阶段时间线</h3>
              <div className="flex gap-2">
                <button
                  className="grid size-9 place-items-center rounded-md border border-line"
                  title="刷新"
                  onClick={() => store.refreshRun()}
                >
                  <RefreshCw size={16} />
                </button>
                <button
                  className="grid size-9 place-items-center rounded-md border border-line"
                  title="继续"
                  disabled={!store.run || store.run.status !== "paused"}
                  onClick={handleResume}
                >
                  <Play size={16} />
                </button>
                <button
                  className="grid size-9 place-items-center rounded-md border border-line"
                  title="取消"
                  disabled={!store.run}
                  onClick={() => store.cancelRun()}
                >
                  <Square size={16} />
                </button>
              </div>
            </div>
            <div className="grid gap-2 md:grid-cols-4">
              {timeline.map(([id, label]) => {
                const active = currentStage === id || (id === "human_gate" && gateRequired);
                const done = store.events.some(
                  (event) => event.stage === id && event.type.includes("completed"),
                );
                return (
                  <div
                    key={id}
                    className={`rounded-md border p-3 ${
                      active ? "border-accent bg-[#eef9f6]" : "border-line bg-panel"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{label}</span>
                      {done ? (
                        <Check size={16} className="text-accent" />
                      ) : active ? (
                        <Activity size={16} className="text-accent" />
                      ) : null}
                    </div>
                    <p className="mt-2 text-xs text-muted">{id}</p>
                  </div>
                );
              })}
            </div>
            <div className="mt-4">
              <WorkflowGraph currentStage={currentStage} gateRequired={gateRequired} />
            </div>
          </div>

          {/* Events */}
          <div className="rounded-md border border-line bg-white p-4 shadow-soft">
            <h3 className="mb-3 font-semibold">RunEvent</h3>
            <div className="studio-scroll max-h-72 space-y-2 overflow-auto">
              {store.events.length === 0 ? (
                <p className="text-sm text-muted">暂无事件</p>
              ) : null}
              {store.events.map((event) => (
                <div key={event.id} className="rounded-md border border-line bg-panel p-3">
                  <div className="flex items-center justify-between gap-3">
                    <strong className="text-sm">{event.stage}</strong>
                    <span
                      className={`rounded px-2 py-1 text-xs ${
                        event.severity === "warning"
                          ? "bg-[#fff7ed] text-amber"
                          : "bg-white text-muted"
                      }`}
                    >
                      {event.type}
                    </span>
                  </div>
                  <p className="mt-2 text-sm">{event.message}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Human Gate */}
          <div className="rounded-md border border-line bg-white p-4 shadow-soft">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="font-semibold">Human Gate</h3>
              {gateRequired ? (
                <span className="rounded bg-[#fff7ed] px-2 py-1 text-xs text-amber">等待确认</span>
              ) : null}
            </div>
            {gateRequired ? (
              <div className="space-y-3">
                {store.gate?.artifact_previews && store.gate.artifact_previews.length > 0 ? (
                  store.gate.artifact_previews.map((preview) => (
                    <details key={preview.path} className="rounded-md border border-line bg-panel">
                      <summary className="cursor-pointer px-3 py-2 text-sm font-medium text-muted">
                        {preview.path}
                      </summary>
                      <pre className="max-h-48 overflow-auto border-t border-line bg-white px-3 py-2 text-xs whitespace-pre-wrap">
                        {preview.content}
                      </pre>
                    </details>
                  ))
                ) : (
                  <div className="rounded-md border border-line bg-panel p-3 text-sm">
                    <p className="font-medium">推荐路线：方案 A</p>
                    <p className="mt-2 text-muted">
                      优先完成可解释模型和稳健性分析，保留备选路线用于修订阶段。
                    </p>
                  </div>
                )}
                <label className="grid gap-1 text-sm">
                  选定路线
                  <input
                    className="h-10 rounded-md border border-line px-3"
                    value={store.selectedRoute}
                    onChange={(e) => store.setSelectedRoute(e.target.value)}
                    placeholder="方案 A"
                  />
                </label>
                <label className="grid gap-1 text-sm">
                  人工备注
                  <textarea
                    className="h-20 rounded-md border border-line px-3 py-2"
                    value={store.humanNotes}
                    onChange={(e) => store.setHumanNotes(e.target.value)}
                    placeholder="补充说明、修改意见或风险提示..."
                  />
                </label>
                <div className="grid gap-2 sm:grid-cols-3">
                  <button
                    className="h-10 rounded-md bg-accent text-white"
                    onClick={() => store.submitGate("approved")}
                  >
                    批准
                  </button>
                  <button
                    className="h-10 rounded-md border border-line"
                    onClick={() => store.submitGate("alternative")}
                  >
                    备选
                  </button>
                  <button
                    className="h-10 rounded-md border border-line"
                    onClick={() => store.submitGate("custom")}
                  >
                    自定义
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted">当前没有人工闸门</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
