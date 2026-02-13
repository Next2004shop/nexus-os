"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  variant?: "default" | "danger";
  className?: string;
}

export function Modal({ open, onClose, title, children, variant = "default", className }: ModalProps) {
  const backdropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleEsc);
    return () => document.removeEventListener("keydown", handleEsc);
  }, [open, onClose]);

  if (!open) return null;

  const borderColor =
    variant === "danger"
      ? "border-[var(--nexus-red)]/30"
      : "border-[var(--nexus-border)]";

  return (
    <div
      ref={backdropRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === backdropRef.current) onClose();
      }}
    >
      <div
        className={cn(
          "nexus-card w-full max-w-md p-6 animate-fade-in",
          borderColor,
          className
        )}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-mono font-semibold">{title}</h3>
          <button
            onClick={onClose}
            className="text-[var(--nexus-subtext)] hover:text-[var(--foreground)] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
