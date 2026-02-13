import type { Metadata } from "next";
import { Sidebar } from "@/components/Sidebar";
import { TopBar } from "@/components/TopBar";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import "./globals.css";

export const metadata: Metadata = {
  title: "NEXUS_OS — Sovereign Trading Platform",
  description: "Multi-Agent Council AI Trading System",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-[var(--background)] text-[var(--foreground)] antialiased">
        <Sidebar />
        <TopBar />
        <main className="ml-[var(--sidebar-width)] mt-[var(--topbar-height)] min-h-[calc(100vh-var(--topbar-height))] p-6">
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </body>
    </html>
  );
}
