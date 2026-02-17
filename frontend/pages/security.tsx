import Head from 'next/head'
import Layout from '@/components/Layout'
import { motion } from 'framer-motion'

const measures = [
  { icon: '🔐', title: 'Encrypted Authentication', desc: 'JWT tokens with HS256 signing, bcrypt-hashed passwords, and secure HTTP-only cookie storage.' },
  { icon: '🛡️', title: 'Rate Limiting', desc: 'Built-in rate limiting middleware protects against brute-force attacks and API abuse.' },
  { icon: '🔒', title: 'Data Isolation', desc: 'Every user\'s agents, tasks, and data are strictly isolated — no cross-account access is possible.' },
  { icon: '📡', title: 'TLS Encryption', desc: 'All data in transit is encrypted via TLS. Database connections use secure protocols.' },
  { icon: '🧪', title: 'Code Sandboxing', desc: 'Agent-generated code executes in isolated sandboxed environments to prevent system-level access.' },
  { icon: '📋', title: 'Audit Logging', desc: 'Comprehensive request logging and monitoring for anomaly detection and incident response.' },
]

export default function Security() {
  return (
    <Layout>
      <Head><title>Security | OmniDev AI</title></Head>

      <section className="min-h-screen pt-32 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <h1 className="text-5xl font-bold text-white mb-4">
              <span className="gradient-text">Security</span>
            </h1>
            <p className="text-lg text-slate-400 mb-12">Security is foundational to OmniDev AI. Here&apos;s how we protect your account and data.</p>
          </motion.div>

          <div className="grid sm:grid-cols-2 gap-6 mb-12">
            {measures.map((m, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.08 }}
                className="glass-strong rounded-2xl p-6 border border-white/5"
              >
                <div className="text-2xl mb-3">{m.icon}</div>
                <h3 className="text-lg font-semibold text-white mb-2">{m.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{m.desc}</p>
              </motion.div>
            ))}
          </div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.6 }}
            className="glass-strong rounded-2xl p-8 text-center">
            <h2 className="text-2xl font-bold text-white mb-3">Found a vulnerability?</h2>
            <p className="text-slate-400 mb-4">We take security reports seriously. Please report any issues responsibly.</p>
            <a href="mailto:security@omnidev.ai" className="btn-primary !inline-flex text-sm">
              security@omnidev.ai
            </a>
          </motion.div>
        </div>
      </section>
    </Layout>
  )
}
