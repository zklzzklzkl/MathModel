"use client";

import {
  Boxes,
  FileText,
  FlaskConical,
  GraduationCap,
  Library,
  Play,
  Activity,
  Upload,
} from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useStudioStore, domains, runtimeDrivers } from "@/store/useStudioStore";

const domainIcons: Record<string, typeof FlaskConical> = {
  math_modeling: FlaskConical,
  statistics: Activity,
  data_analysis: Boxes,
  paper_writing: FileText,
  homework: GraduationCap,
  research: Library,
};

export default function StudioHome() {
  const router = useRouter();
  const store = useStudioStore();
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  async function handleCreateAndRun() {
    await store.createProject(uploadFile);
    const p = useStudioStore.getState().project;
    if (p) {
      await useStudioStore.getState().startRun();
      router.push("/runs");
    }
  }

  return (
    <div className="space-y-6">
      {/* Domain selector */}
      <section>
        <h2 className="mb-3 text-lg font-semibold text-ink">选择任务类型</h2>
        <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-6">
          {domains.map((item) => {
            const Icon = domainIcons[item.id] ?? FlaskConical;
            const active = store.selectedDomain === item.id;
            return (
              <button
                key={item.id}
                className={`h-24 rounded-md border px-3 text-left transition ${
                  active ? "border-accent bg-[#eef9f6]" : "border-line bg-white hover:bg-panel"
                }`}
                onClick={() => store.setSelectedDomain(item.id)}
                title={item.label}
              >
                <Icon size={20} />
                <span className="mt-3 block text-sm font-medium leading-tight">{item.label}</span>
              </button>
            );
          })}
        </div>
      </section>

      {/* Project creation */}
      <section className="rounded-md border border-line bg-white p-4 shadow-soft">
        <h2 className="mb-4 text-lg font-semibold text-ink">创建项目</h2>
        <div className="grid gap-3 lg:grid-cols-[1fr_160px_190px]">
          <label className="grid gap-1 text-sm">
            项目名称
            <input
              className="h-10 rounded-md border border-line px-3"
              value={store.projectName}
              onChange={(e) => store.setProjectName(e.target.value)}
            />
          </label>
          <label className="grid gap-1 text-sm">
            赛事/分类
            <input
              className="h-10 rounded-md border border-line px-3"
              value={store.contest}
              onChange={(e) => store.setContest(e.target.value)}
            />
          </label>
          <label className="grid gap-1 text-sm">
            资料上传
            <input
              className="h-10 rounded-md border border-line px-3 py-2 text-xs"
              type="file"
              onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
            />
          </label>
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-[1fr_180px_180px]">
          <label className="grid gap-1 text-sm">
            运行引擎
            <select
              className="h-10 rounded-md border border-line px-3"
              value={store.driver}
              onChange={(e) => store.setDriver(e.target.value)}
            >
              {runtimeDrivers.map(([id, label]) => (
                <option key={id} value={id}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <Button disabled={store.busy} onClick={() => store.createProject(uploadFile)}>
            <Upload size={17} />
            创建项目
          </Button>
          <Button variant="accent" disabled={store.busy || !store.project} onClick={handleCreateAndRun}>
            <Play size={17} />
            创建并运行
          </Button>
        </div>
      </section>

      {/* Quick links */}
      {store.project ? (
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <button
            className="rounded-md border border-line bg-white p-4 text-left shadow-soft hover:border-accent"
            onClick={() => router.push("/runs")}
          >
            <Play size={20} className="text-accent" />
            <p className="mt-2 font-semibold text-ink">运行管理</p>
            <p className="text-sm text-muted">查看阶段时间线和运行事件</p>
          </button>
          <button
            className="rounded-md border border-line bg-white p-4 text-left shadow-soft hover:border-accent"
            onClick={() => router.push("/projects")}
          >
            <Upload size={20} className="text-cobalt" />
            <p className="mt-2 font-semibold text-ink">制品浏览</p>
            <p className="text-sm text-muted">查看 workspace 文件和报告</p>
          </button>
          <button
            className="rounded-md border border-line bg-white p-4 text-left shadow-soft hover:border-accent"
            onClick={() => router.push("/templates")}
          >
            <FileText size={20} className="text-cobalt" />
            <p className="mt-2 font-semibold text-ink">模板库</p>
            <p className="text-sm text-muted">管理论文模板包</p>
          </button>
          <button
            className="rounded-md border border-line bg-white p-4 text-left shadow-soft hover:border-accent"
            onClick={() => router.push("/quality")}
          >
            <Activity size={20} className="text-cobalt" />
            <p className="mt-2 font-semibold text-ink">质量检查</p>
            <p className="text-sm text-muted">V2 评分和审计面板</p>
          </button>
        </section>
      ) : null}
    </div>
  );
}
