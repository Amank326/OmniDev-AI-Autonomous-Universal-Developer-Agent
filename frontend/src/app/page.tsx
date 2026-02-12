import Link from 'next/link';
import { ArrowRight, Zap, Brain, Code2, Gauge } from 'lucide-react';

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-black/50 backdrop-blur-md border-b border-slate-700 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Zap className="w-8 h-8 text-blue-400" />
            <span className="text-xl font-bold">OmniDev AI</span>
          </div>
          <div className="flex gap-4">
            <Link href="/auth/login" className="px-4 py-2 rounded-lg hover:bg-slate-700 transition">
              Sign In
            </Link>
            <Link href="/auth/signup" className="px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 transition">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="text-center mt-20 mb-16 max-w-4xl">
        <h1 className="text-6xl font-bold mb-6 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
          AI-Powered Development Platform
        </h1>
        <p className="text-xl text-slate-300 mb-8">
          Deploy intelligent agents that build, analyze, and optimize your applications automatically.
        </p>
        <Link
          href="/auth/signup"
          className="inline-flex items-center gap-2 px-8 py-4 bg-blue-600 rounded-lg hover:bg-blue-700 transition text-lg font-semibold"
        >
          Start Building <ArrowRight className="w-5 h-5" />
        </Link>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl">
        {[
          {
            icon: Brain,
            title: 'AI Agents',
            description: 'Deploy intelligent agents for code generation, analysis, and DevOps',
          },
          {
            icon: Code2,
            title: 'Code Generation',
            description: 'Automatically generate, review, and optimize code',
          },
          {
            icon: Gauge,
            title: 'Real-time Monitoring',
            description: 'Monitor agent execution and performance in real-time',
          },
          {
            icon: Zap,
            title: 'Fast Execution',
            description: 'Run tasks instantly with our optimized infrastructure',
          },
        ].map((feature, i) => (
          <div
            key={i}
            className="p-6 rounded-xl bg-slate-800/50 border border-slate-700 hover:border-blue-500 transition group"
          >
            <feature.icon className="w-8 h-8 text-blue-400 mb-3 group-hover:scale-110 transition" />
            <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
            <p className="text-slate-400 text-sm">{feature.description}</p>
          </div>
        ))}
      </div>

      {/* CTA Section */}
      <div className="mt-20 text-center">
        <p className="text-slate-400 mb-4">Ready to build something amazing?</p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg hover:from-blue-700 hover:to-purple-700 transition font-semibold"
        >
          Go to Dashboard <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </main>
  );
}
