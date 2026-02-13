import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

interface CardProps {
  title?: string;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
  headerRight?: ReactNode;
}

export function Card({ title, icon, children, className, headerRight }: CardProps) {
  return (
    <div className={cn("nexus-card p-4", className)}>
      {(title || icon) && (
        <div className="flex items-center justify-between mb-3">
          <h3 className="flex items-center gap-2 text-[var(--nexus-subtext)] text-[11px] font-mono uppercase tracking-wider">
            {icon}
            {title}
          </h3>
          {headerRight}
        </div>
      )}
      {children}
    </div>
  );
}
