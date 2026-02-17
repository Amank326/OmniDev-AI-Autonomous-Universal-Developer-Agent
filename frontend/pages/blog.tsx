import Head from 'next/head'
import Link from 'next/link'
import Layout from '@/components/Layout'
import { motion } from 'framer-motion'

const posts = [
  {
    title: 'Introducing OmniDev AI: The Future of Autonomous Development',
    excerpt: 'We\'re excited to launch OmniDev AI — a platform that brings autonomous AI agents to every stage of the software development lifecycle.',
    date: '2025-01-15',
    tag: 'Announcement',
  },
  {
    title: 'How AI Code Review Agents Catch Bugs Before Production',
    excerpt: 'Learn how our code review agent uses static analysis combined with LLM reasoning to identify subtle bugs, security vulnerabilities, and code smells.',
    date: '2025-01-10',
    tag: 'Engineering',
  },
  {
    title: 'Building Scalable Agent Pipelines with OmniDev',
    excerpt: 'A deep dive into chaining multiple AI agents together — from code generation through testing and deployment — in a single automated pipeline.',
    date: '2025-01-05',
    tag: 'Tutorial',
  },
]

export default function Blog() {
  return (
    <Layout>
      <Head><title>Blog | OmniDev AI</title></Head>

      <section className="min-h-screen pt-32 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <h1 className="text-5xl font-bold text-white mb-4">
              <span className="gradient-text">Blog</span>
            </h1>
            <p className="text-lg text-slate-400 mb-12">Engineering updates, tutorials, and announcements from the OmniDev team.</p>
          </motion.div>

          <div className="space-y-6">
            {posts.map((post, i) => (
              <motion.article
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="glass-strong rounded-2xl p-8 hover:border-purple-500/30 border border-white/5 transition-all duration-300 cursor-pointer"
              >
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-purple-500/20 text-purple-400">{post.tag}</span>
                  <span className="text-xs text-slate-600">{post.date}</span>
                </div>
                <h2 className="text-xl font-bold text-white mb-2 hover:text-purple-400 transition">{post.title}</h2>
                <p className="text-slate-400 text-sm leading-relaxed">{post.excerpt}</p>
              </motion.article>
            ))}
          </div>

          <div className="text-center mt-12">
            <p className="text-slate-500 text-sm">More posts coming soon. Stay tuned!</p>
          </div>
        </div>
      </section>
    </Layout>
  )
}
