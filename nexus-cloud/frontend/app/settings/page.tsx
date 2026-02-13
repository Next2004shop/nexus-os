"use client";

import { Settings, Server, Key, Globe, Bell } from "lucide-react";
import { Card } from "@/components/ui/Card";

export default function SettingsPage() {
  return (
    <div className="space-y-6 animate-fade-in max-w-3xl">
      <h1 className="text-lg font-mono font-bold tracking-wide">Settings</h1>

      {/* API Configuration */}
      <Card title="Backend Connection" icon={<Server className="w-3.5 h-3.5" />}>
        <div className="space-y-3">
          <div>
            <label className="text-[10px] text-[var(--nexus-subtext)] uppercase font-mono block mb-1">
              API Endpoint
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"}
                className="flex-1 px-3 py-2 text-xs font-mono bg-[var(--nexus-card)] border border-[var(--nexus-border)] rounded-md outline-none"
              />
              <span className="px-2 py-1 text-[10px] font-mono bg-white/[0.04] rounded text-[var(--nexus-subtext)]">
                ENV
              </span>
            </div>
          </div>
          <p className="text-[11px] text-[var(--nexus-subtext)]">
            Configured via NEXT_PUBLIC_API_URL environment variable. Cannot be changed at runtime.
          </p>
        </div>
      </Card>

      {/* Security */}
      <Card title="Security" icon={<Key className="w-3.5 h-3.5" />}>
        <div className="space-y-2.5 text-xs">
          {[
            { label: "Secrets Storage", value: "Google Secret Manager", status: "ok" },
            { label: "Auth Provider", value: "Firebase", status: "ok" },
            { label: "Trade Signing", value: "HMAC-SHA256 (MT Bridge)", status: "ok" },
            { label: "Frontend Access", value: "READ-ONLY", status: "ok" },
            { label: "API Keys on Frontend", value: "NEVER", status: "ok" },
          ].map((item) => (
            <div key={item.label} className="flex justify-between py-1.5 border-b border-[var(--nexus-border)]">
              <span className="text-[var(--nexus-subtext)]">{item.label}</span>
              <span className="font-mono text-[var(--nexus-green)]">{item.value}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Deployment */}
      <Card title="Deployment" icon={<Globe className="w-3.5 h-3.5" />}>
        <div className="space-y-2.5 text-xs">
          {[
            { label: "Platform", value: "Google Cloud Run" },
            { label: "Project ID", value: "nexus-dyron-777" },
            { label: "Region", value: "us-central1" },
            { label: "Backend Memory", value: "2 GiB / 2 CPU" },
            { label: "Frontend Memory", value: "512 MiB / 1 CPU" },
            { label: "Min Instances", value: "1" },
          ].map((item) => (
            <div key={item.label} className="flex justify-between py-1.5 border-b border-[var(--nexus-border)]">
              <span className="text-[var(--nexus-subtext)]">{item.label}</span>
              <span className="font-mono">{item.value}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Notifications */}
      <Card title="Notifications" icon={<Bell className="w-3.5 h-3.5" />}>
        <div className="space-y-3">
          <div className="flex justify-between items-center py-1.5">
            <span className="text-xs text-[var(--nexus-subtext)]">Telegram Bot</span>
            <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-[var(--nexus-yellow)]/10 text-[var(--nexus-yellow)]">
              DEFERRED (Phase E.2)
            </span>
          </div>
          <p className="text-[11px] text-[var(--nexus-subtext)]">
            Telegram notifications are planned for Phase E.2. The backend has a notification stub ready for integration.
          </p>
        </div>
      </Card>
    </div>
  );
}
