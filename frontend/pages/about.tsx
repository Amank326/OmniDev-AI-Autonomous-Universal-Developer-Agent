import Head from 'next/head'
import Link from 'next/link'
import Layout from '@/components/Layout'
import { motion } from 'framer-motion'

const team = [
  { name: 'OmniDev Team', role: 'Core Development', desc: 'Building the future of AI-powered development tooling.' },
]

export default function About() {
  return (
    <Layout>
      <Head><title>About | OmniDev AI</title></Head>

      <section className="min-h-screen pt-32 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <h1 className="text-5xl font-bold text-white mb-6">
              About <span className="gradient-text">OmniDev AI</span>
            </h1>
            <p className="text-lg text-slate-400 leading-relaxed mb-12">
              OmniDev AI is an autonomous, AI-powered universal developer agent platform. We empower developers to ship
              production-quality code 10x faster using intelligent agents that analyze, generate, review, debug, refactor,
              and deploy code — all from a single unified interface.
            </p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.2 }}
            className="glass-strong rounded-2xl p-8 mb-12">
            <h2 className="text-2xl font-bold text-white mb-4">Our Mission</h2>
            <p className="text-slate-400 leading-relaxed">
              To democratize software development by providing every developer — from solo builders to enterprise teams —
              with autonomous AI agents that handle the repetitive, complex, and time-consuming parts of the development
              lifecycle, so humans can focus on creativity and architecture.
            </p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.4 }}
            className="glass-strong rounded-2xl p-8 mb-12">
            <h2 className="text-2xl font-bold text-white mb-4">What We Do</h2>
            <ul className="space-y-3 text-slate-400">
              <li className="flex items-start gap-3"><span className="text-purple-400 mt-1">●</span> AI-powered code generation, review, and refactoring</li>
              <li className="flex items-start gap-3"><span className="text-cyan-400 mt-1">●</span> Autonomous debugging and testing agents</li>
              <li className="flex items-start gap-3"><span className="text-pink-400 mt-1">●</span> Intelligent documentation generation</li>
              <li className="flex items-start gap-3"><span className="text-purple-400 mt-1">●</span> One-click deployment automation</li>
              <li className="flex items-start gap-3"><span className="text-cyan-400 mt-1">●</span> Real-time collaboration and notifications</li>
            </ul>
          </motion.div>

          <div className="text-center">
            <Link href="/auth/register" className="btn-primary text-base">
              Get Started Free →
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  )
}
