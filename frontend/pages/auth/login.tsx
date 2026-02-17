import { useState } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import Link from 'next/link'
import Cookies from 'js-cookie'
import { authAPI } from '@/lib/api'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'

export default function Login() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  })
  const [loading, setLoading] = useState(false)
  const [focused, setFocused] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await authAPI.login(formData)
      const { access_token, refresh_token } = response.data

      Cookies.set('auth_token', access_token, { expires: 1, sameSite: 'Lax' })
      Cookies.set('refresh_token', refresh_token, { expires: 7, sameSite: 'Lax' })

      toast.success('Login successful!')
      router.push('/dashboard')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Head>
        <title>Login — OmniDev AI</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
      </Head>

      <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-dark-950">
        {/* Background Effects */}
        <div className="absolute inset-0 bg-grid opacity-20" />
        <div className="orb orb-purple w-[400px] h-[400px] -top-32 -left-32 animate-pulse-glow" />
        <div className="orb orb-cyan w-[350px] h-[350px] bottom-20 -right-20 animate-pulse-glow" style={{ animationDelay: '2s' }} />
        <div className="orb orb-pink w-[250px] h-[250px] top-1/2 left-1/3 animate-pulse-glow" style={{ animationDelay: '4s' }} />

        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
          className="relative z-10 w-full max-w-md mx-4"
        >
          <div className="glass-strong rounded-2xl p-8 sm:p-10 relative overflow-hidden">
            {/* Gradient border overlay */}
            <div className="absolute inset-0 rounded-2xl p-[1px] -z-10">
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-purple-500/20 via-transparent to-cyan-500/20" />
            </div>

            {/* Logo */}
            <div className="flex justify-center mb-8">
              <Link href="/" className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center text-white font-bold text-lg">O</div>
                <span className="text-xl font-bold text-white">Omni<span className="gradient-text">Dev</span></span>
              </Link>
            </div>

            <h1 className="text-2xl font-bold text-white text-center mb-2">Welcome Back</h1>
            <p className="text-sm text-slate-400 text-center mb-8">Sign in to continue to your dashboard</p>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                  Email
                </label>
                <div className={`relative rounded-xl transition-all duration-300 ${focused === 'email' ? 'ring-1 ring-purple-500/50 shadow-lg shadow-purple-500/10' : ''}`}>
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" /></svg>
                  </div>
                  <input
                    type="email"
                    id="email"
                    required
                    className="input-dark !pl-11"
                    placeholder="you@example.com"
                    value={formData.email}
                    onFocus={() => setFocused('email')}
                    onBlur={() => setFocused('')}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <label htmlFor="password" className="block text-sm font-medium text-slate-300">
                    Password
                  </label>
                  <a href="#" className="text-xs text-purple-400 hover:text-purple-300 transition">Forgot?</a>
                </div>
                <div className={`relative rounded-xl transition-all duration-300 ${focused === 'password' ? 'ring-1 ring-purple-500/50 shadow-lg shadow-purple-500/10' : ''}`}>
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" /></svg>
                  </div>
                  <input
                    type="password"
                    id="password"
                    required
                    className="input-dark !pl-11"
                    placeholder="••••••••"
                    value={formData.password}
                    onFocus={() => setFocused('password')}
                    onBlur={() => setFocused('')}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  />
                </div>
              </div>

              <motion.button
                type="submit"
                disabled={loading}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                className="btn-primary w-full justify-center !rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                    Signing in...
                  </div>
                ) : 'Sign In'}
              </motion.button>
            </form>

            {/* Divider */}
            <div className="flex items-center gap-4 my-6">
              <div className="flex-1 h-px bg-white/5" />
              <span className="text-xs text-slate-600">or</span>
              <div className="flex-1 h-px bg-white/5" />
            </div>

            {/* Social Buttons (placeholder) */}
            <div className="grid grid-cols-2 gap-3">
              <button className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl border border-white/5 bg-white/[0.02] text-sm text-slate-300 hover:bg-white/5 hover:border-white/10 transition-all">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                GitHub
              </button>
              <button className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl border border-white/5 bg-white/[0.02] text-sm text-slate-300 hover:bg-white/5 hover:border-white/10 transition-all">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" /><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" /><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" /><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" /></svg>
                Google
              </button>
            </div>

            <p className="text-center mt-6 text-sm text-slate-500">
              Don&apos;t have an account?{' '}
              <Link href="/auth/register" className="text-purple-400 hover:text-purple-300 font-medium transition">
                Sign up
              </Link>
            </p>
          </div>
        </motion.div>
      </div>
    </>
  )
}
