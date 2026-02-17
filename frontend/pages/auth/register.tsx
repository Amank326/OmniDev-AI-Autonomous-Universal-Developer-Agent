import { useState } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import Link from 'next/link'
import { authAPI } from '@/lib/api'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'

export default function Register() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    full_name: '',
  })
  const [loading, setLoading] = useState(false)
  const [focused, setFocused] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      await authAPI.register(formData)
      toast.success('Registration successful! Please login.')
      router.push('/auth/login')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const fields = [
    { id: 'full_name', label: 'Full Name', type: 'text', placeholder: 'John Doe', required: false, icon: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" /></svg> },
    { id: 'username', label: 'Username', type: 'text', placeholder: 'johndoe', required: true, icon: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 9h3.75M15 12h3.75M15 15h3.75M4.5 19.5h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5zm6-10.125a1.875 1.875 0 11-3.75 0 1.875 1.875 0 013.75 0zm1.294 6.336a6.721 6.721 0 01-3.17.789 6.721 6.721 0 01-3.168-.789 3.376 3.376 0 016.338 0z" /></svg> },
    { id: 'email', label: 'Email', type: 'email', placeholder: 'you@example.com', required: true, icon: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" /></svg> },
    { id: 'password', label: 'Password', type: 'password', placeholder: '••••••••', required: true, icon: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" /></svg> },
  ]

  return (
    <>
      <Head>
        <title>Register — OmniDev AI</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
      </Head>

      <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-dark-950">
        {/* Background Effects */}
        <div className="absolute inset-0 bg-grid opacity-20" />
        <div className="orb orb-cyan w-[400px] h-[400px] -top-32 -right-32 animate-pulse-glow" />
        <div className="orb orb-purple w-[350px] h-[350px] bottom-20 -left-20 animate-pulse-glow" style={{ animationDelay: '2s' }} />
        <div className="orb orb-pink w-[200px] h-[200px] top-1/3 right-1/3 animate-pulse-glow" style={{ animationDelay: '4s' }} />

        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
          className="relative z-10 w-full max-w-md mx-4 my-12"
        >
          <div className="glass-strong rounded-2xl p-8 sm:p-10 relative overflow-hidden">
            <div className="absolute inset-0 rounded-2xl p-[1px] -z-10">
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyan-500/20 via-transparent to-purple-500/20" />
            </div>

            {/* Logo */}
            <div className="flex justify-center mb-8">
              <Link href="/" className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center text-white font-bold text-lg">O</div>
                <span className="text-xl font-bold text-white">Omni<span className="gradient-text">Dev</span></span>
              </Link>
            </div>

            <h1 className="text-2xl font-bold text-white text-center mb-2">Create Account</h1>
            <p className="text-sm text-slate-400 text-center mb-8">Start building with AI agents today</p>

            <form onSubmit={handleSubmit} className="space-y-4">
              {fields.map((field) => (
                <div key={field.id}>
                  <label htmlFor={field.id} className="block text-sm font-medium text-slate-300 mb-1.5">
                    {field.label}
                  </label>
                  <div className={`relative rounded-xl transition-all duration-300 ${focused === field.id ? 'ring-1 ring-purple-500/50 shadow-lg shadow-purple-500/10' : ''}`}>
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                      {field.icon}
                    </div>
                    <input
                      type={field.type}
                      id={field.id}
                      required={field.required}
                      minLength={field.id === 'password' ? 8 : undefined}
                      className="input-dark !pl-11"
                      placeholder={field.placeholder}
                      value={(formData as any)[field.id]}
                      onFocus={() => setFocused(field.id)}
                      onBlur={() => setFocused('')}
                      onChange={(e) => setFormData({ ...formData, [field.id]: e.target.value })}
                    />
                  </div>
                  {field.id === 'password' && (
                    <p className="text-xs text-slate-600 mt-1">Minimum 8 characters</p>
                  )}
                </div>
              ))}

              <motion.button
                type="submit"
                disabled={loading}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                className="btn-primary w-full justify-center !rounded-xl disabled:opacity-50 disabled:cursor-not-allowed mt-6"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                    Creating account...
                  </div>
                ) : (
                  <>
                    Create Account
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </>
                )}
              </motion.button>
            </form>

            <p className="text-center mt-6 text-sm text-slate-500">
              Already have an account?{' '}
              <Link href="/auth/login" className="text-purple-400 hover:text-purple-300 font-medium transition">
                Sign in
              </Link>
            </p>
          </div>
        </motion.div>
      </div>
    </>
  )
}
