"use client";

import { useStudioStore } from "@/store/useStudioStore";
import { ArtifactPreview } from "@/components/artifact-preview";
import { FileTree } from "@/components/files/FileTree";

export default function ProjectsPage() {
  const store = useStudioStore();

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-ink">项目制品</h2>
      {!store.project ? (
        <p className="text-sm text-muted">请先在首页创建项目</p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
          <FileTree />
          <ArtifactPreview
            title={store.selectedArtifactPath ? `制品预览 · ${store.selectedArtifactPath}` : "制品预览"}
            value={
              store.artifactPreview?.content ??
              `# ${store.project.name}\n\nworkspace: ${store.project.workspace_path}\n\n保留文件化证据层：reports / code / figures / results / paper。`
            }
          />
        </div>
      )}
    </div>
  );
}
