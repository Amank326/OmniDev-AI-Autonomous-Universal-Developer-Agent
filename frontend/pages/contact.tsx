import Head from 'next/head'
import Layout from '@/components/Layout'
import { motion } from 'framer-motion'
import { useState } from 'react'
import toast from 'react-hot-toast'

export default function Contact() {
  const [form, setForm] = useState({ name: '', email: '', message: '' })
  const [sending, setSending] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name || !form.email || !form.message) {
      toast.error('Please fill in all fields')
      return
    }
    setSending(true)
    setTimeout(() => {
      toast.success('Message sent! We\'ll get back to you soon.')
      setForm({ name: '', email: '', message: '' })
      setSending(false)
    }, 1000)
  }

  return (
    <Layout>
      <Head><title>Contact | OmniDev AI</title></Head>

      <section className="min-h-screen pt-32 pb-20 px-4">
        <div className="max-w-2xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <h1 className="text-5xl font-bold text-white mb-4">
              Get in <span className="gradient-text">Touch</span>
            </h1>
            <p className="text-lg text-slate-400 mb-12">Have a question, feedback, or partnership inquiry? We&apos;d love to hear from you.</p>
          </motion.div>

          <motion.form
            onSubmit={handleSubmit}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="glass-strong rounded-2xl p-8 space-y-6"
          >
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Name</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 outline-none transition"
                placeholder="Your name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Email</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 outline-none transition"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Message</label>
              <textarea
                value={form.message}
                onChange={(e) => setForm({ ...form, message: e.target.value })}
                rows={5}
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 outline-none transition resize-none"
                placeholder="How can we help?"
              />
            </div>
            <button type="submit" disabled={sending} className="btn-primary w-full !justify-center">
              {sending ? 'Sending…' : 'Send Message'}
            </button>
          </motion.form>
        </div>
      </section>
    </Layout>
  )
}
