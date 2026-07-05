"use client";

import { X } from "lucide-react";
import { useEffect } from "react";
import { useStudioStore, type ToastMessage } from "@/store/useStudioStore";

function ToastItem({ toast }: { toast: ToastMessage }) {
  const dismissToast = useStudioStore((s) => s.dismissToast);

  useEffect(() => {
    const timer = setTimeout(() => dismissToast(toast.id), 5000);
    return () => clearTimeout(timer);
  }, [toast.id, dismissToast]);

  const colors: Record<string, string> = {
    info: "border-cobalt bg-[#eef4ff]",
    success: "border-accent bg-[#eef9f6]",
    warning: "border-amber bg-[#fff7ed]",
    error: "border-rose bg-[#fef2f2]",
  };

  return (
    <div className={`flex items-start gap-2 rounded-md border-l-4 px-3 py-2 shadow-soft ${colors[toast.severity] ?? colors.info}`}>
      <p className="flex-1 text-sm text-ink">{toast.message}</p>
      <button className="text-muted hover:text-ink" onClick={() => dismissToast(toast.id)}>
        <X size={14} />
      </button>
    </div>
  );
}

export function ToastContainer() {
  const toasts = useStudioStore((s) => s.toasts);
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 grid gap-2 max-w-sm">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} />
      ))}
    </div>
  );
}
