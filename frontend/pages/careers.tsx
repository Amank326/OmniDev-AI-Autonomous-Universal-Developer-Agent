import Head from 'next/head'
import Layout from '@/components/Layout'
import { motion } from 'framer-motion'

const openings = [
  { title: 'Senior Full-Stack Engineer', location: 'Remote', type: 'Full-time' },
  { title: 'ML/AI Engineer — Agent Systems', location: 'Remote', type: 'Full-time' },
  { title: 'Developer Advocate', location: 'Remote', type: 'Full-time' },
]

export default function Careers() {
  return (
    <Layout>
      <Head><title>Careers | OmniDev AI</title></Head>

      <section className="min-h-screen pt-32 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <h1 className="text-5xl font-bold text-white mb-4">
              Join <span className="gradient-text">OmniDev AI</span>
            </h1>
            <p className="text-lg text-slate-400 mb-12">Help us build the next generation of AI-powered developer tools. We&apos;re remote-first and mission-driven.</p>
          </motion.div>

          <div className="space-y-4 mb-12">
            {openings.map((job, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="glass-strong rounded-2xl p-6 flex items-center justify-between border border-white/5 hover:border-purple-500/30 transition-all duration-300"
              >
                <div>
                  <h3 className="text-lg font-semibold text-white">{job.title}</h3>
                  <p className="text-sm text-slate-500">{job.location} · {job.type}</p>
                </div>
                <button className="text-sm text-purple-400 hover:text-purple-300 font-medium transition">Apply →</button>
              </motion.div>
            ))}
          </div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.4 }}
            className="glass-strong rounded-2xl p-8 text-center">
            <h2 className="text-2xl font-bold text-white mb-3">Don&apos;t see your role?</h2>
            <p className="text-slate-400 mb-4">We&apos;re always looking for talented people. Send us your resume and we&apos;ll keep you in mind.</p>
            <a href="mailto:careers@omnidev.ai" className="btn-primary !inline-flex text-sm">
              careers@omnidev.ai
            </a>
          </motion.div>
        </div>
      </section>
    </Layout>
  )
}
