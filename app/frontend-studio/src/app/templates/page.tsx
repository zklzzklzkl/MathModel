"use client";

import { AlertTriangle } from "lucide-react";
import { useState } from "react";
import { useStudioStore } from "@/store/useStudioStore";
import { apiFetch, templateDownloadUrl, type TemplatePack } from "@/lib/api";

export default function TemplatesPage() {
  const templates = useStudioStore((s) => s.templates);
  const busy = useStudioStore((s) => s.busy);
  const setBusy = useStudioStore((s) => s.setBusy);
  const setMessage = useStudioStore((s) => s.setMessage);
  const refreshStudioData = useStudioStore((s) => s.refreshStudioData);
  const [templateFile, setTemplateFile] = useState<File | null>(null);

  async function handleUpload() {
    if (!templateFile) return;
    setBusy(true);
    try {
      const form = new FormData();
      form.append("file", templateFile);
      await apiFetch<TemplatePack>("/api/templates/upload", { method: "POST", body: form });
      await refreshStudioData();
      setMessage("模板包已上传");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "模板上传失败");
    } finally {
      setBusy(false);
    }
  }

  async function handleImportBuiltin() {
    setBusy(true);
    try {
      const result = await apiFetch<{ imported_count: number; templates: TemplatePack[] }>(
        "/api/templates/import-builtin",
        { method: "POST", body: "{}" },
      );
      await refreshStudioData();
      setMessage(`已导入 ${result.imported_count} 个内置模板`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "内置模板导入失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-ink">模板库</h2>

      <div className="rounded-md border border-line bg-white p-4 shadow-soft">
        <div className="mb-3 grid grid-cols-[1fr_88px_112px] gap-2">
          <input
            className="h-10 rounded-md border border-line px-2 text-sm"
            type="file"
            accept=".zip"
            onChange={(e) => setTemplateFile(e.target.files?.[0] ?? null)}
          />
          <button
            className="h-10 rounded-md bg-ink text-white disabled:opacity-50"
            disabled={!templateFile || busy}
            onClick={handleUpload}
          >
            上传
          </button>
          <button
            className="h-10 rounded-md border border-line bg-white text-sm disabled:opacity-50"
            disabled={busy}
            onClick={handleImportBuiltin}
          >
            导入内置
          </button>
        </div>
        <div className="studio-scroll max-h-[600px] space-y-2 overflow-auto">
          {templates.length === 0 ? (
            <p className="text-sm text-muted">暂无模板包，请上传 ZIP 或导入内置模板</p>
          ) : null}
          {templates.map((template) => (
            <div key={template.id} className="rounded-md border border-line p-3">
              <div className="flex items-center justify-between">
                <strong className="text-sm">{template.name}</strong>
                <a className="text-xs text-cobalt" href={templateDownloadUrl(template.id)}>
                  下载
                </a>
              </div>
              <p className="mt-1 text-xs text-muted">
                {template.contest} &middot; {template.engine} &middot; {template.main_file}
              </p>
              {template.warnings.length ? (
                <p className="mt-2 flex items-center gap-1 text-xs text-amber">
                  <AlertTriangle size={13} />
                  {template.warnings[0]}
                </p>
              ) : null}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
