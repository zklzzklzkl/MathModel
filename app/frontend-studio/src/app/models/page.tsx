"use client";

import { Settings } from "lucide-react";
import { useStudioStore } from "@/store/useStudioStore";
import type { StageModelConfig } from "@/lib/api";

export default function ModelsPage() {
  const modelConfig = useStudioStore((s) => s.modelConfig);
  const updateStageConfig = useStudioStore((s) => s.updateStageConfig);

  if (!modelConfig) return null;

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-ink">模型设置</h2>
      <div className="rounded-md border border-line bg-white p-4 shadow-soft">
        <div className="mb-3 flex items-center gap-2">
          <Settings size={18} />
          <h3 className="font-semibold">阶段模型配置</h3>
        </div>
        <div className="studio-scroll max-h-[640px] space-y-3 overflow-auto pr-1">
          {modelConfig.stages.map((stage) => (
            <div key={stage.stage} className="rounded-md border border-line p-3">
              <div className="mb-2 flex items-center justify-between">
                <strong className="text-sm">{stage.label}</strong>
                <span className="text-xs text-muted">T {stage.temperature}</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <select
                  className="h-9 rounded-md border border-line px-2 text-sm"
                  value={stage.provider}
                  onChange={(e) => updateStageConfig(stage, { provider: e.target.value })}
                >
                  {modelConfig.providers.map((provider) => (
                    <option key={provider.id} value={provider.id}>
                      {provider.label}
                    </option>
                  ))}
                </select>
                <input
                  className="h-9 rounded-md border border-line px-2 text-sm"
                  value={stage.model}
                  placeholder="model"
                  onChange={(e) => updateStageConfig(stage, { model: e.target.value })}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
