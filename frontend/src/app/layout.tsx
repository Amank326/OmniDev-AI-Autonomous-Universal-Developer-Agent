import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'OmniDev AI - Full-Stack Platform',
  description: 'Build intelligent applications with AI agents',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-black text-white antialiased">
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-black">
          {children}
        </div>
      </body>
    </html>
  );
}
