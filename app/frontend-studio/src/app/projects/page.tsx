"use client";

import { useStudioStore } from "@/store/useStudioStore";
import { ArtifactPreview } from "@/components/artifact-preview";

export default function ProjectsPage() {
  const store = useStudioStore();

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-ink">项目制品</h2>
      {!store.project ? (
        <p className="text-sm text-muted">请先在首页创建项目</p>
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
            {/* Artifact index */}
            <div className="rounded-md border border-line bg-white p-4 shadow-soft">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-semibold">制品索引</h3>
                <button className="text-xs text-cobalt" onClick={() => store.refreshArtifacts()}>
                  刷新
                </button>
              </div>
              <div className="studio-scroll max-h-[460px] space-y-2 overflow-auto">
                {store.artifacts.length === 0 ? (
                  <p className="text-sm text-muted">暂无制品</p>
                ) : null}
                {store.artifacts.map((artifact) => (
                  <button
                    key={artifact.path}
                    className={`block w-full rounded-md border px-3 py-2 text-left text-xs ${
                      store.selectedArtifactPath === artifact.path
                        ? "border-accent bg-[#eef9f6]"
                        : "border-line bg-panel"
                    }`}
                    onClick={() => store.readArtifactPath(artifact.path)}
                    title={artifact.path}
                  >
                    <span className="block truncate font-medium">{artifact.path}</span>
                    <span className="text-muted">
                      {artifact.type} &middot; {artifact.size} B
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Preview */}
            <ArtifactPreview
              title={store.selectedArtifactPath ? `制品预览 · ${store.selectedArtifactPath}` : "制品预览"}
              value={
                store.artifactPreview?.content ??
                `# ${store.project.name}\n\nworkspace: ${store.project.workspace_path}\n\n保留文件化证据层：reports / code / figures / results / paper。`
              }
            />
          </div>
        </>
      )}
    </div>
  );
}
