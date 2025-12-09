import { cn } from "@/lib/utils";
import React from "react";

export function Card({ className, children }: { className?: string; children: React.ReactNode }) {
    return (
        <div className={cn("glass rounded-2xl border border-nexus-border overflow-hidden", className)}>
            {children}
        </div>
    );
}
