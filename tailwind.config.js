/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'nexus-black': '#050505',
        'nexus-gray': '#121212',
        'nexus-card': '#1E1E1E',
        'nexus-border': '#2A2A2A',
        'nexus-text': '#FFFFFF',
        'nexus-subtext': '#888888',
        'nexus-yellow': '#F0B90B',
        'nexus-green': '#00FF94', // Neon Green
        'nexus-red': '#FF2E54',   // Neon Red
        'nexus-blue': '#00F0FF',  // Neon Blue
      },
      animation: {
        'fadeIn': 'fadeIn 0.3s ease-out',
        'slideUp': 'slideUp 0.4s ease-out',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(0, 240, 255, 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(0, 240, 255, 0.6), 0 0 10px rgba(0, 240, 255, 0.4)' },
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'], // Main font
        mono: ['JetBrains Mono', 'monospace'], // Numbers/Code
      }
    },
  },
  plugins: [],
}