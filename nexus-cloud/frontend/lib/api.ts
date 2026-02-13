const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "Unknown error");
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

// Health & Status
export const api = {
  getHealth: () => request<{ status: string }>("/health"),

  getStatus: () =>
    request<{
      council: Record<string, unknown>;
      ensemble: Record<string, unknown>;
      stealth: Record<string, unknown>;
      risk: Record<string, unknown>;
      execution: Record<string, unknown>;
    }>("/status"),

  getRiskStatus: () => request<Record<string, unknown>>("/risk-status"),

  // Dashboard data
  getEquityCurve: () =>
    request<{ curve: { timestamp: string; equity: number }[] }>(
      "/dashboard/equity-curve"
    ),

  getPositions: () =>
    request<{ positions: Record<string, unknown>[] }>("/dashboard/positions"),

  getOrders: () =>
    request<{ orders: Record<string, unknown>[] }>("/dashboard/orders"),

  // Trading
  placeTrade: (symbol: string, side: string, quantity: number, marketContext = {}) =>
    request<Record<string, unknown>>("/trade", {
      method: "POST",
      body: JSON.stringify({ symbol, side, quantity, market_context: marketContext }),
    }),

  killSwitch: () =>
    request<Record<string, unknown>>("/kill", { method: "POST" }),

  resume: () =>
    request<Record<string, unknown>>("/resume", { method: "POST" }),

  // Analysis
  analyze: (symbol: string, data: Record<string, unknown> = {}) =>
    request<Record<string, unknown>>("/analyze", {
      method: "POST",
      body: JSON.stringify({ symbol, data }),
    }),

  // AI
  aiCommand: (command: string) =>
    request<Record<string, unknown>>("/ai/command", {
      method: "POST",
      body: JSON.stringify({ command }),
    }),

  getAiStatus: () => request<Record<string, unknown>>("/ai/status"),

  // Market data
  getTick: (symbol: string) =>
    request<Record<string, unknown>>(`/data/tick/${symbol}`),
};
