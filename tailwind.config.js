/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        nexus: {
          black: '#1E2329', // Binance Main BG
          dark: '#0B0E11',  // Darker BG
          card: '#1E2329',  // Card BG
          gray: '#474D57',  // Subtext
          border: '#2B3139', // Borders
          yellow: '#FCD535', // Primary Action
          green: '#0ECB81', // Buy/Up
          red: '#F6465D',   // Sell/Down
          text: '#EAECEF',  // Main Text
          subtext: '#848E9C' // Secondary Text
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