import Head from 'next/head'
import Layout from '@/components/Layout'
import { motion } from 'framer-motion'

export default function Privacy() {
  return (
    <Layout>
      <Head><title>Privacy Policy | OmniDev AI</title></Head>

      <section className="min-h-screen pt-32 pb-20 px-4">
        <div className="max-w-3xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <h1 className="text-5xl font-bold text-white mb-4">Privacy <span className="gradient-text">Policy</span></h1>
            <p className="text-sm text-slate-500 mb-12">Last updated: January 2025</p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.2 }}
            className="prose prose-invert max-w-none space-y-8">
            <div className="glass-strong rounded-2xl p-8">
              <h2 className="text-xl font-bold text-white mb-3">1. Information We Collect</h2>
              <p className="text-slate-400 leading-relaxed">We collect information you provide directly — such as your name, email address, and username when you create an account. We also collect usage data including which agents you create, task execution logs, and general platform interaction metrics.</p>
            </div>

            <div className="glass-strong rounded-2xl p-8">
              <h2 className="text-xl font-bold text-white mb-3">2. How We Use Your Information</h2>
              <p className="text-slate-400 leading-relaxed">Your information is used to provide, maintain, and improve OmniDev AI services. This includes authenticating your account, executing AI agent tasks, sending notifications, and improving our AI models. We do not sell your personal information to third parties.</p>
            </div>

            <div className="glass-strong rounded-2xl p-8">
              <h2 className="text-xl font-bold text-white mb-3">3. Data Security</h2>
              <p className="text-slate-400 leading-relaxed">We implement industry-standard security measures including encrypted connections (TLS), hashed passwords (bcrypt), and token-based authentication (JWT). Your code and project data are isolated per-user and never shared across accounts.</p>
            </div>

            <div className="glass-strong rounded-2xl p-8">
              <h2 className="text-xl font-bold text-white mb-3">4. Your Rights</h2>
              <p className="text-slate-400 leading-relaxed">You may request access to, correction of, or deletion of your personal data at any time by contacting us. You can also delete your account from the dashboard settings, which will permanently remove all associated data.</p>
            </div>

            <div className="glass-strong rounded-2xl p-8">
              <h2 className="text-xl font-bold text-white mb-3">5. Contact</h2>
              <p className="text-slate-400 leading-relaxed">For privacy-related questions, contact us at <a href="mailto:privacy@omnidev.ai" className="text-purple-400 hover:text-purple-300">privacy@omnidev.ai</a>.</p>
            </div>
          </motion.div>
        </div>
      </section>
    </Layout>
  )
}
