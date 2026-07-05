"use client";

import "@xyflow/react/dist/style.css";
import { Background, Controls, ReactFlow, type Edge, type Node } from "@xyflow/react";

type WorkflowGraphProps = {
  currentStage: string;
  gateRequired: boolean;
};

const phaseNodes = [
  ["problem_intake", "题面建档"],
  ["model_strategy", "建模策略"],
  ["human_gate", "人工确认"],
  ["code_generation", "代码实验"],
  ["paper_writing", "论文构建"],
  ["contest_review", "竞赛评审"],
  ["revision", "修订"],
  ["final_verify", "最终验收"],
] as const;

export function WorkflowGraph({ currentStage, gateRequired }: WorkflowGraphProps) {
  const nodes: Node[] = phaseNodes.map(([id, label], index) => {
    const active = currentStage === id || (id === "human_gate" && gateRequired);
    return {
      id,
      data: { label },
      position: { x: (index % 4) * 190, y: Math.floor(index / 4) * 120 },
      style: {
        width: 150,
        borderRadius: 8,
        border: active ? "2px solid #0f766e" : "1px solid #dbe2ea",
        background: active ? "#eef9f6" : "#ffffff",
        color: "#16202a",
        fontSize: 13,
        fontWeight: active ? 700 : 500,
      },
    };
  });
  const edges: Edge[] = phaseNodes.slice(0, -1).map(([id], index) => ({
    id: `${id}-${phaseNodes[index + 1][0]}`,
    source: id,
    target: phaseNodes[index + 1][0],
    animated: phaseNodes[index + 1][0] === currentStage,
    style: { stroke: "#8a97a5" },
  }));

  return (
    <div className="h-[285px] rounded-md border border-line bg-white">
      <ReactFlow nodes={nodes} edges={edges} fitView nodesDraggable={false} nodesConnectable={false} panOnScroll zoomOnScroll={false}>
        <Background gap={18} color="#e8edf2" />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
