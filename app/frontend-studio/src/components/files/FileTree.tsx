"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  FileSpreadsheet,
  FileJson,
  FileText,
  FileImage,
  File as FileIcon,
  FileCode2,
  FolderOpen,
  Upload,
  Trash2,
  Plus,
} from "lucide-react";
import { useStudioStore } from "@/store/useStudioStore";
import { buildTree, extType, formatSize, type FileInfo, type TreeNode } from "@/lib/file-tree";
import { ImageLightbox } from "@/components/files/ImageLightbox";

const FILE_ICONS: Record<string, React.ReactNode> = {
  pdf: <FileText className="h-4 w-4 text-red-400" />,
  spreadsheet: <FileSpreadsheet className="h-4 w-4 text-green-400" />,
  json: <FileJson className="h-4 w-4 text-yellow-400" />,
  html: <FileText className="h-4 w-4 text-orange-500" />,
  latex: <FileText className="h-4 w-4 text-orange-400" />,
  code: <FileCode2 className="h-4 w-4 text-blue-400" />,
  image: <FileImage className="h-4 w-4 text-purple-400" />,
  text: <FileText className="h-4 w-4 text-blue-400" />,
};

const SECTION_LABELS: Record<string, string> = {
  source: "上传材料 source/",
  reports: "报告 reports/",
  results: "结果 results/",
  code: "代码 code/",
  figures: "图表 figures/",
  paper: "论文 paper/",
  workspace: "其他文件",
};

export function FileTree() {
  const artifacts = useStudioStore((s) => s.artifacts);
  const selectedArtifactPath = useStudioStore((s) => s.selectedArtifactPath);
  const project = useStudioStore((s) => s.project);
  const refreshArtifacts = useStudioStore((s) => s.refreshArtifacts);
  const readArtifactPath = useStudioStore((s) => s.readArtifactPath);
  const setBusy = useStudioStore((s) => s.setBusy);
  const setMessage = useStudioStore((s) => s.setMessage);

  const inputRef = useRef<HTMLInputElement>(null);
  const [imagePreview, setImagePreview] = useState<{ src: string; name: string } | null>(null);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());

  const fileList: FileInfo[] = artifacts.map((a) => ({
    path: a.path,
    type: a.type,
    size: a.size,
  }));

  useEffect(() => {
    if (project?.id) refreshArtifacts(project.id);
  }, [project?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleUpload = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const fileList = e.target.files;
      if (!fileList || fileList.length === 0 || !project?.id) return;
      setBusy(true);
      try {
        const form = new FormData();
        Array.from(fileList).forEach((f) => form.append("files", f));
        const { apiFetch } = await import("@/lib/api");
        await apiFetch(`/api/projects/${project.id}/files`, { method: "POST", body: form });
        await refreshArtifacts(project.id);
        setMessage("文件已上传");
      } catch (err) {
        setMessage(err instanceof Error ? err.message : "上传失败");
      } finally {
        setBusy(false);
        if (inputRef.current) inputRef.current.value = "";
      }
    },
    [project?.id, refreshArtifacts, setBusy, setMessage],
  );

  const handleFileClick = useCallback(
    async (file: FileInfo) => {
      if (!project?.id) return;
      const type = extType(file.path);
      if (type === "image") {
        const API_BASE = process.env.NEXT_PUBLIC_MATHMODEL_API_BASE ?? "http://127.0.0.1:8000";
        setImagePreview({
          src: `${API_BASE}/api/projects/${project.id}/artifacts/read?path=${encodeURIComponent(file.path)}`,
          name: file.path,
        });
        return;
      }
      await readArtifactPath(file.path, project.id);
    },
    [project?.id, readArtifactPath],
  );

  const handleDelete = useCallback(
    async (path: string, e: React.MouseEvent) => {
      e.stopPropagation();
      // Note: V3 doesn't have dedicated delete endpoint yet — UI only for now
    },
    [],
  );

  useEffect(() => {
    if (!imagePreview) return;
    const stillExists = fileList.some((f) => f.path === imagePreview.name);
    if (!stillExists) setImagePreview(null);
  }, [fileList, imagePreview]);

  // Group files by top-level directory
  const sections: Record<string, FileInfo[]> = {};
  for (const f of fileList) {
    const top = f.path.split("/")[0] || "workspace";
    if (!sections[top]) sections[top] = [];
    sections[top].push(f);
  }

  const toggleDir = useCallback((dirPath: string) => {
    setExpandedDirs((prev) => {
      const next = new Set(prev);
      if (next.has(dirPath)) next.delete(dirPath);
      else next.add(dirPath);
      return next;
    });
  }, []);

  const renderFileRow = (file: FileInfo, displayName?: string) => {
    const active = selectedArtifactPath === file.path;
    const iconType = extType(file.path);
    return (
      <button
        key={file.path}
        onClick={() => handleFileClick(file)}
        className={`group flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left transition-all ${
          active
            ? "bg-ink text-white shadow-soft"
            : "text-ink hover:bg-panel hover:shadow-sm"
        }`}
      >
        <span
          className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-panel ring-1 ring-line/70 ${
            active && "bg-white/10 ring-white/15"
          }`}
        >
          {FILE_ICONS[iconType] ?? <FileIcon className="h-4 w-4 text-muted" />}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-xs font-medium">{displayName ?? file.path}</span>
          <span className={`block truncate text-[10px] ${active ? "text-white/60" : "text-muted/70"}`}>
            {file.type.toUpperCase()}
          </span>
        </span>
        <span
          className={`rounded-full px-1.5 py-0.5 text-[9px] ${
            active ? "bg-white/10 text-white/70" : "bg-panel text-muted"
          }`}
        >
          {formatSize(file.size)}
        </span>
      </button>
    );
  };

  const renderTreeNode = (node: TreeNode, depth: number, pathPrefix: string) => {
    const sortedChildren = Array.from(node.children.values()).sort((a, b) => {
      const aIsDir = a.children.size > 0 && !a.file;
      const bIsDir = b.children.size > 0 && !b.file;
      if (aIsDir !== bIsDir) return aIsDir ? -1 : 1;
      return a.name.localeCompare(b.name);
    });

    return sortedChildren.map((child) => {
      const childPath = pathPrefix ? `${pathPrefix}/${child.name}` : child.name;
      const isDir = child.children.size > 0 && !child.file;
      const isExpanded = expandedDirs.has(childPath);

      if (isDir) {
        return (
          <div key={childPath}>
            <button
              onClick={() => toggleDir(childPath)}
              className="group flex w-full items-center gap-1.5 rounded-md px-2 py-1.5 text-left transition-colors hover:bg-panel"
              style={{ paddingLeft: `${8 + depth * 12}px` }}
            >
              <svg
                className={`h-3 w-3 text-muted/60 transition-transform ${isExpanded ? "rotate-90" : ""}`}
                viewBox="0 0 12 12"
                fill="none"
              >
                <path
                  d="M4.5 2L8.5 6L4.5 10"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <FolderOpen className="h-3.5 w-3.5 text-amber" />
              <span className="flex-1 truncate text-xs font-medium text-muted">{child.name}</span>
            </button>
            {isExpanded && <div>{renderTreeNode(child, depth + 1, childPath)}</div>}
          </div>
        );
      }

      if (child.file) {
        return (
          <div key={child.file.path} style={{ paddingLeft: `${depth * 12}px` }}>
            {renderFileRow(child.file, child.name)}
          </div>
        );
      }
      return null;
    });
  };

  const renderSection = (title: string, files: FileInfo[]) => {
    if (files.length === 0) return null;
    const tree = buildTree(files);
    return (
      <section className="rounded-md border border-line bg-white p-2 shadow-soft">
        <div className="mb-1 flex items-center justify-between px-1.5 py-1">
          <div className="flex min-w-0 items-center gap-1.5">
            <FolderOpen className="h-3.5 w-3.5 shrink-0 text-muted" />
            <span className="truncate text-[10px] font-semibold uppercase tracking-wider text-muted">
              {title}
            </span>
          </div>
          <span className="rounded-full bg-panel px-1.5 py-0.5 text-[9px] font-medium text-muted">
            {files.length}
          </span>
        </div>
        <div className="space-y-1">{renderTreeNode(tree, 0, "")}</div>
      </section>
    );
  };

  return (
    <div className="flex flex-col rounded-md border border-line bg-white shadow-soft">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-1.5">
          <FolderOpen className="h-4 w-4 text-ink" />
          <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">
            项目文件
          </span>
        </div>
        <button
          onClick={() => inputRef.current?.click()}
          className="rounded-full border border-line bg-white p-1.5 text-muted shadow-soft transition-colors hover:bg-ink hover:text-white"
          title="上传文件"
        >
          <Plus className="h-3.5 w-3.5" />
        </button>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.csv,.xlsx,.xls,.json,.txt,.psv,.tsv,.html,.htm,.parquet,.tex,.cls,.sty,.typ,.png,.jpg,.jpeg,.py,.md,.bib"
          onChange={handleUpload}
          className="hidden"
        />
      </div>

      {/* File list */}
      <div className="flex flex-col gap-2 px-2 pb-3">
        {fileList.length === 0 ? (
          <button
            onClick={() => inputRef.current?.click()}
            className="flex flex-col items-center gap-2 rounded-md border border-dashed border-line bg-panel px-3 py-5 text-muted transition-colors hover:border-ink/40 hover:bg-white"
          >
            <Upload className="h-5 w-5 opacity-40" />
            <span className="text-[11px]">上传文件</span>
            <span className="text-[10px] opacity-50">
              支持 PDF, CSV, XLSX, JSON, TXT, LaTeX, Python, Markdown 等
            </span>
          </button>
        ) : (
          Object.entries(sections).map(([key, files]) =>
            renderSection(SECTION_LABELS[key] ?? key, files),
          )
        )}
      </div>

      {imagePreview && (
        <ImageLightbox
          src={imagePreview.src}
          alt={imagePreview.name}
          onClose={() => setImagePreview(null)}
        />
      )}
    </div>
  );
}
