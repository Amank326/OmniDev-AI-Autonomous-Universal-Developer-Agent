import { ReactNode } from 'react'
import Navbar from './Navbar'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col bg-dark-950 noise-overlay">
      <Navbar />
      <main className="flex-1 relative z-10">{children}</main>
    </div>
  )
}
