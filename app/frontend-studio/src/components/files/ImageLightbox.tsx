"use client";

import { useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

interface ImageLightboxProps {
  src: string;
  alt?: string;
  onClose: () => void;
}

export function ImageLightbox({ src, alt = "图表预览", onClose }: ImageLightboxProps) {
  const handleClose = useCallback(
    (e?: React.MouseEvent) => {
      e?.preventDefault();
      e?.stopPropagation();
      onClose();
    },
    [onClose],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [onClose]);

  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  if (typeof document === "undefined") return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[2147483000] flex flex-col bg-black/90"
      role="dialog"
      aria-modal="true"
      aria-label="图片预览"
    >
      <div className="flex shrink-0 items-center justify-between gap-3 border-b border-white/15 bg-black/80 px-4 py-3">
        <span className="min-w-0 truncate text-sm text-white/90">{alt}</span>
        <button
          type="button"
          className="flex shrink-0 items-center gap-1.5 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-black shadow-lg transition-colors hover:bg-white/90"
          onClick={handleClose}
          aria-label="关闭预览"
        >
          <X className="h-4 w-4" />
          关闭
        </button>
      </div>
      <div
        className="relative flex min-h-0 flex-1 items-center justify-center p-4"
        onClick={handleClose}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={src}
          alt={alt}
          className="max-h-full max-w-full select-none object-contain"
          onClick={(e) => e.stopPropagation()}
          draggable={false}
        />
      </div>
      <div className="shrink-0 border-t border-white/15 bg-black/80 px-4 py-2 text-center text-xs text-white/70">
        按 Esc 键，或点击空白区域关闭
      </div>
    </div>,
    document.body,
  );
}
