import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "var(--background)",
                foreground: "var(--foreground)",
                nexus: {
                    bg: "var(--nexus-bg)",
                    card: "var(--nexus-card)",
                    border: "var(--nexus-border)",
                    green: "var(--nexus-green)",
                    "green-glow": "var(--nexus-green-glow)",
                    red: "var(--nexus-red)",
                    "red-glow": "var(--nexus-red-glow)",
                    blue: "var(--nexus-blue)",
                    yellow: "var(--nexus-yellow)",
                    subtext: "var(--nexus-subtext)",
                },
            },
            fontFamily: {
                sans: ["var(--font-inter)", "sans-serif"],
                mono: ["var(--font-jetbrains)", "monospace"],
            },
            backgroundImage: {
                "nexus-gradient": "radial-gradient(circle at 10% 20%, rgba(0, 221, 128, 0.05) 0%, transparent 40%), radial-gradient(circle at 90% 80%, rgba(10, 132, 255, 0.05) 0%, transparent 40%)",
            },
        },
    },
    plugins: [],
};
export default config;
