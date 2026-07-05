"use client";

import { Send, Sparkles, ChevronUp, MessageSquare, Trash2, Loader2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { useStudioStore } from "@/store/useStudioStore";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export function BottomChat() {
  const project = useStudioStore((s) => s.project);
  const run = useStudioStore((s) => s.run);
  const [expanded, setExpanded] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    const controller = new AbortController();
    controllerRef.current = controller;

    try {
      const API_BASE = process.env.NEXT_PUBLIC_MATHMODEL_API_BASE ?? "http://127.0.0.1:8000";
      const ctx = {
        projectId: project?.id ?? null,
        projectName: project?.name ?? null,
        domain: project?.domain ?? null,
        runId: run?.id ?? null,
        runStage: run?.current_stage ?? null,
      };
      const resp = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, context: ctx }),
        signal: controller.signal,
      });

      if (!resp.ok) throw new Error("Chat failed");

      const reader = resp.body?.getReader();
      if (!reader) throw new Error("No stream");

      const decoder = new TextDecoder();
      let buffer = "";
      let assistantContent = "";

      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.content) {
                assistantContent += data.content;
                setMessages((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1] = { role: "assistant", content: assistantContent };
                  return updated;
                });
              }
              if (data.done) break;
            } catch {
              // skip malformed SSE
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: `错误: ${(err as Error).message}`,
          };
          return updated;
        });
      }
    } finally {
      setLoading(false);
      controllerRef.current = null;
    }
  }, [input, loading, project, run]);

  const handleClear = () => {
    controllerRef.current?.abort();
    setMessages([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-line bg-white">
      {/* Collapsed bar */}
      {!expanded && (
        <button
          onClick={() => setExpanded(true)}
          className="flex w-full items-center gap-2 px-4 py-2 text-sm text-muted transition-colors hover:bg-panel hover:text-ink"
        >
          <MessageSquare size={15} />
          <span className="flex-1 text-left">AI 助手</span>
          <span className="text-xs">点击展开</span>
          <ChevronUp size={14} className="rotate-180" />
        </button>
      )}

      {/* Expanded panel */}
      {expanded && (
        <div className="flex flex-col" style={{ height: "320px" }}>
          {/* Header */}
          <div className="flex items-center justify-between border-b border-line px-4 py-2">
            <div className="flex items-center gap-2">
              <Sparkles size={15} className="text-accent" />
              <span className="text-sm font-medium text-ink">AI 助手</span>
              {loading && <Loader2 size={14} className="animate-spin text-muted" />}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleClear}
                className="rounded p-1 text-muted transition-colors hover:bg-panel hover:text-ink"
                title="清空对话"
              >
                <Trash2 size={14} />
              </button>
              <button
                onClick={() => setExpanded(false)}
                className="rounded p-1 text-muted transition-colors hover:bg-panel hover:text-ink"
              >
                <ChevronUp size={16} />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {messages.length === 0 ? (
              <p className="text-center text-xs text-muted py-8">
                向 AI 助手提问，获取建模建议、代码帮助或结果解读
              </p>
            ) : (
              messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex gap-2 ${msg.role === "user" ? "justify-end" : ""}`}
                >
                  {msg.role === "assistant" && (
                    <div className="grid size-6 shrink-0 place-items-center rounded-full bg-accent/10">
                      <Sparkles size={12} className="text-accent" />
                    </div>
                  )}
                  <div
                    className={`rounded-lg px-3 py-2 text-sm max-w-[85%] ${
                      msg.role === "user"
                        ? "bg-ink text-white"
                        : "bg-panel text-ink"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <div className="prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1">
                        <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                          {msg.content || "..."}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                  </div>
                  {msg.role === "user" && (
                    <div className="grid size-6 shrink-0 place-items-center rounded-full bg-ink">
                      <MessageSquare size={12} className="text-white" />
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Input */}
          <div className="border-t border-line px-4 py-2">
            <div className="flex items-center gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入消息..."
                disabled={loading}
                className="flex-1 rounded-md border border-line bg-panel px-3 py-2 text-sm text-ink placeholder:text-muted focus:outline-none focus:border-accent disabled:opacity-50"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || loading}
                className="grid size-9 place-items-center rounded-md bg-accent text-white disabled:opacity-50"
              >
                <Send size={15} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
