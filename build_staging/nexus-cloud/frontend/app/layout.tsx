import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import Sidebar from '@/components/Sidebar'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const jetbrains = JetBrains_Mono({ subsets: ['latin'], variable: '--font-jetbrains' })

export const metadata: Metadata = {
  title: 'Nexus AI | Enterprise Trading',
  description: 'Advanced AI-Powered Trading Platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${jetbrains.variable} font-sans flex h-screen bg-nexus-bg text-nexus-text overflow-hidden selection:bg-nexus-green/30`}>
        <Sidebar />
        <main className="flex-1 overflow-hidden relative bg-nexus-gradient">
          <div className="absolute inset-0 bg-nexus-gradient opacity-50 pointer-events-none" />
          {children}
        </main>
      </body>
    </html>
  )
}
