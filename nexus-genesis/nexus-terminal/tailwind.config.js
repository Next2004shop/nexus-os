/** @type {import('tailwindcss').Config} */
export default {
    content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
    theme: {
        extend: {
            fontFamily: {
                mono: ['JetBrains Mono', 'monospace'],
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
            colors: {
                nexus: {
                    bg: '#0a0a0f',
                    surface: '#111116',
                    border: '#1e1e2a',
                    hover: '#16161f',
                    accent: '#3b82f6',
                    green: '#22c55e',
                    red: '#ef4444',
                    amber: '#f59e0b',
                    muted: '#6b7280',
                    text: '#e5e7eb',
                },
            },
        },
    },
    plugins: [],
}
