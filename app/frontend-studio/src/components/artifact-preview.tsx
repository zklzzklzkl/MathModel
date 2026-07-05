"use client";

import dynamic from "next/dynamic";

const MonacoEditor = dynamic(() => import("@monaco-editor/react").then((module) => module.Editor), {
  ssr: false,
  loading: () => <div className="grid h-[240px] place-items-center rounded-md border border-line bg-panel text-sm text-muted">加载预览器</div>,
});

type ArtifactPreviewProps = {
  title: string;
  value: string;
};

export function ArtifactPreview({ title, value }: ArtifactPreviewProps) {
  return (
    <div className="rounded-md border border-line bg-white p-4 shadow-soft">
      <h3 className="mb-3 font-semibold">{title}</h3>
      <MonacoEditor
        height="240px"
        defaultLanguage="markdown"
        value={value}
        options={{
          readOnly: true,
          minimap: { enabled: false },
          fontSize: 13,
          lineNumbers: "off",
          scrollBeyondLastLine: false,
          wordWrap: "on",
        }}
      />
    </div>
  );
}
