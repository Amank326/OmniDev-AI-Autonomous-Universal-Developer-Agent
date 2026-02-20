import Head from 'next/head'
import Link from 'next/link'
import dynamic from 'next/dynamic'
import { motion } from 'framer-motion'
import { ScrollReveal, StaggerContainer, StaggerItem, CountUp } from '@/components/ScrollAnimations'
import ParticleField from '@/components/ParticleField'

const HeroOrb = dynamic(() => import('@/components/HeroOrb'), { ssr: false })

const FEATURES = [
  {
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" /></svg>
    ),
    title: 'AI Code Agents',
    desc: 'Autonomous agents that analyze, generate, review, and refactor code across any language or framework.',
    gradient: 'from-purple-500/20 to-purple-500/5',
    iconColor: 'text-purple-400',
  },
  {
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" /></svg>
    ),
    title: 'Real-Time Execution',
    desc: 'Live code execution with WebSocket streaming. Watch your AI agents work in real-time with instant feedback.',
    gradient: 'from-cyan-500/20 to-cyan-500/5',
    iconColor: 'text-cyan-400',
  },
  {
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" /></svg>
    ),
    title: 'Enterprise Security',
    desc: 'JWT auth, bcrypt hashing, rate limiting, CORS, role-based access control, and encrypted data at rest.',
    gradient: 'from-green-500/20 to-green-500/5',
    iconColor: 'text-green-400',
  },
  {
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" /></svg>
    ),
    title: 'Smart Notifications',
    desc: 'Multi-channel alerts via email, SMS, push, and WebSocket. Customizable triggers and delivery rules.',
    gradient: 'from-pink-500/20 to-pink-500/5',
    iconColor: 'text-pink-400',
  },
  {
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" /></svg>
    ),
    title: 'Stripe Billing',
    desc: 'Subscription management, usage-based billing, invoicing, and payment processing — production-ready.',
    gradient: 'from-blue-500/20 to-blue-500/5',
    iconColor: 'text-blue-400',
  },
  {
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" /></svg>
    ),
    title: 'Cloud-Native Stack',
    desc: 'Docker, Kubernetes-ready. PostgreSQL, Redis, Celery task queues, and horizontal auto-scaling.',
    gradient: 'from-orange-500/20 to-orange-500/5',
    iconColor: 'text-orange-400',
  },
]

const AGENTS = [
  {
    name: 'CodeGen Agent',
    role: 'Full-Stack Code Generator',
    desc: 'Generates production-ready code in Python, TypeScript, Rust, Go, and 20+ languages. Understands architecture patterns and best practices.',
    status: 'Active',
    color: 'purple',
    icon: '⚡',
    tasks: '12.4K',
  },
  {
    name: 'Review Agent',
    role: 'Code Review & Security Audit',
    desc: 'Performs deep code review, identifies bugs, security vulnerabilities, performance issues, and suggests optimized solutions.',
    status: 'Active',
    color: 'cyan',
    icon: '🔍',
    tasks: '8.7K',
  },
  {
    name: 'Doc Agent',
    role: 'Documentation & API Docs',
    desc: 'Auto-generates comprehensive documentation, API references, changelogs, and README files from your codebase.',
    status: 'Active',
    color: 'pink',
    icon: '📝',
    tasks: '5.2K',
  },
  {
    name: 'Debug Agent',
    role: 'Intelligent Debugger',
    desc: 'Traces errors through stack traces, identifies root causes, suggests fixes, and can auto-patch simple bugs.',
    status: 'Active',
    color: 'green',
    icon: '🐛',
    tasks: '9.1K',
  },
  {
    name: 'Refactor Agent',
    role: 'Code Refactoring & Optimization',
    desc: 'Restructures code for better readability, performance, and maintainability while preserving behavior.',
    status: 'Active',
    color: 'blue',
    icon: '🔄',
    tasks: '6.8K',
  },
  {
    name: 'Deploy Agent',
    role: 'CI/CD & Deployment Automation',
    desc: 'Manages Docker builds, CI/CD pipelines, cloud deployments, and infrastructure-as-code generation.',
    status: 'Active',
    color: 'orange',
    icon: '🚀',
    tasks: '3.5K',
  },
]

const PRICES = [
  {
    name: 'Starter',
    price: '0',
    desc: 'Perfect for individual developers',
    features: ['3 AI Agent runs/day', '1 project workspace', 'Community support', 'Basic code generation', 'Email notifications'],
    cta: 'Start Free',
    featured: false,
  },
  {
    name: 'Pro',
    price: '29',
    desc: 'For professional developers & teams',
    features: ['Unlimited AI Agent runs', '10 project workspaces', 'Priority support', 'All 6 AI agents', 'Real-time WebSocket', 'API access', 'Custom triggers'],
    cta: 'Start Pro Trial',
    featured: true,
  },
  {
    name: 'Enterprise',
    price: '99',
    desc: 'For organizations at scale',
    features: ['Everything in Pro', 'Unlimited workspaces', 'Dedicated support', 'Custom AI model fine-tuning', 'SSO / SAML', 'Audit logging', 'SLA guarantee', 'On-premise option'],
    cta: 'Contact Sales',
    featured: false,
  },
]

const STATS = [
  { value: 50000, suffix: '+', label: 'Lines Generated', icon: '💻' },
  { value: 99, suffix: '%', label: 'Uptime SLA', icon: '📊' },
  { value: 15, suffix: 'ms', label: 'Avg Latency', icon: '⚡' },
  { value: 6, suffix: '', label: 'AI Agents', icon: '🤖' },
]

export default function Home() {
  return (
    <>
      <Head>
        <title>OmniDev AI — Autonomous Universal Developer Agent</title>
        <meta name="description" content="Next-generation AI development platform with autonomous agents for code generation, review, debugging, and deployment." />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <ParticleField count={50} />

      {/* ========================== HERO SECTION ========================== */}
      <section className="relative min-h-screen flex items-center overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0 bg-grid opacity-30" />
        <div className="orb orb-purple w-[500px] h-[500px] -top-40 -left-40 animate-pulse-glow" />
        <div className="orb orb-cyan w-[400px] h-[400px] top-1/3 -right-32 animate-pulse-glow" style={{ animationDelay: '1.5s' }} />
        <div className="orb orb-pink w-[300px] h-[300px] bottom-20 left-1/4 animate-pulse-glow" style={{ animationDelay: '3s' }} />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid lg:grid-cols-2 gap-12 items-center relative z-10 pt-24">
          {/* Left — Text */}
          <div>
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: [0.25, 0.1, 0.25, 1] }}
            >
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass border border-purple-500/20 text-sm text-purple-300 mb-6">
                <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
                Powered by Advanced AI Agents
              </div>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.15 }}
              className="text-5xl sm:text-6xl lg:text-7xl font-extrabold leading-tight mb-6"
            >
              Build Faster
              <br />
              with{' '}
              <span className="gradient-text">
                AI Agents
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="text-lg text-slate-400 max-w-lg mb-8 leading-relaxed"
            >
              Next-generation autonomous developer platform. 6 specialized AI agents that generate, review, debug, document, refactor, and deploy your code — all in real-time.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.45 }}
              className="flex flex-wrap gap-4"
            >
              <Link href="/auth/register" className="btn-primary text-base">
                Get Started Free
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>
              <a href="#features" className="btn-outline text-base">
                Explore Features
              </a>
            </motion.div>

            {/* Trust Indicators */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8, duration: 1 }}
              className="mt-12 flex items-center gap-6 text-sm text-slate-500"
            >
              <div className="flex -space-x-2">
                {[0,1,2,3,4].map(i => (
                  <div key={i} className="w-8 h-8 rounded-full border-2 border-dark-950 bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center text-xs text-white font-bold">
                    {String.fromCharCode(65 + i)}
                  </div>
                ))}
              </div>
              <span>Trusted by <span className="text-white font-medium">2,500+</span> developers</span>
            </motion.div>
          </div>

          {/* Right — 3D Orb */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1.2, delay: 0.3 }}
            className="hidden lg:block h-[550px] relative"
          >
            <HeroOrb />
            {/* Floating badges around orb */}
            <motion.div
              animate={{ y: [-5, 5, -5] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute top-16 right-0 glass-card px-4 py-2 rounded-xl flex items-center gap-2 text-sm"
            >
              <span className="w-2 h-2 rounded-full bg-green-400" />
              <span className="text-green-400 font-medium">6 Agents Active</span>
            </motion.div>
            <motion.div
              animate={{ y: [5, -5, 5] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute bottom-24 left-0 glass-card px-4 py-2 rounded-xl flex items-center gap-2 text-sm"
            >
              <span className="text-cyan-400">⚡</span>
              <span className="text-slate-300">15ms response</span>
            </motion.div>
            <motion.div
              animate={{ y: [-3, 7, -3] }}
              transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute top-1/2 -left-4 glass-card px-4 py-2 rounded-xl flex items-center gap-2 text-sm"
            >
              <span className="text-purple-400">🔒</span>
              <span className="text-slate-300">Enterprise Secure</span>
            </motion.div>
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
        >
          <div className="w-6 h-10 rounded-full border-2 border-white/20 flex justify-center pt-2">
            <div className="w-1 h-2 bg-white/40 rounded-full" />
          </div>
        </motion.div>
      </section>

      {/* ========================== STATS SECTION ========================== */}
      <section className="relative py-20 border-y border-white/5">
        <div className="max-w-6xl mx-auto px-4 grid grid-cols-2 md:grid-cols-4 gap-8">
          {STATS.map((stat, i) => (
            <ScrollReveal key={i} delay={i * 0.1}>
              <div className="text-center">
                <div className="text-3xl mb-2">{stat.icon}</div>
                <div className="text-3xl sm:text-4xl font-bold text-white mb-1">
                  <CountUp end={stat.value} suffix={stat.suffix} />
                </div>
                <div className="text-sm text-slate-500">{stat.label}</div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </section>

      {/* ========================== FEATURES SECTION ========================== */}
      <section id="features" className="relative py-24 sm:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <ScrollReveal>
            <div className="text-center mb-16">
              <span className="text-sm font-medium text-purple-400 tracking-wider uppercase mb-3 block">Features</span>
              <h2 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                Everything You Need to{' '}
                <span className="gradient-text">Ship Faster</span>
              </h2>
              <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                A complete AI-powered development platform with enterprise-grade features built-in from day one.
              </p>
            </div>
          </ScrollReveal>

          <StaggerContainer className="grid md:grid-cols-2 lg:grid-cols-3 gap-6" staggerDelay={0.08}>
            {FEATURES.map((f, i) => (
              <StaggerItem key={i}>
                <div className="glass-card card-hover-line rounded-2xl p-6 h-full">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.gradient} flex items-center justify-center ${f.iconColor} mb-4`}>
                    {f.icon}
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">{f.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
                </div>
              </StaggerItem>
            ))}
          </StaggerContainer>
        </div>
      </section>

      {/* ========================== AGENTS SECTION ========================== */}
      <section id="agents" className="relative py-24 sm:py-32">
        <div className="orb orb-purple w-[400px] h-[400px] top-1/2 -left-48 animate-pulse-glow" />
        <div className="orb orb-cyan w-[300px] h-[300px] top-20 -right-32 animate-pulse-glow" style={{ animationDelay: '2s' }} />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <ScrollReveal>
            <div className="text-center mb-16">
              <span className="text-sm font-medium text-cyan-400 tracking-wider uppercase mb-3 block">AI Agents</span>
              <h2 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                Meet Your{' '}
                <span className="gradient-text-cyan">AI Dev Team</span>
              </h2>
              <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                Six specialized autonomous agents, each a master of their domain. They collaborate in real-time to deliver exceptional results.
              </p>
            </div>
          </ScrollReveal>

          <StaggerContainer className="grid md:grid-cols-2 lg:grid-cols-3 gap-6" staggerDelay={0.1}>
            {AGENTS.map((agent, i) => {
              const colorMap: Record<string, string> = {
                purple: 'from-purple-500/20 to-purple-500/5 border-purple-500/20 hover:border-purple-500/40',
                cyan: 'from-cyan-500/20 to-cyan-500/5 border-cyan-500/20 hover:border-cyan-500/40',
                pink: 'from-pink-500/20 to-pink-500/5 border-pink-500/20 hover:border-pink-500/40',
                green: 'from-green-500/20 to-green-500/5 border-green-500/20 hover:border-green-500/40',
                blue: 'from-blue-500/20 to-blue-500/5 border-blue-500/20 hover:border-blue-500/40',
                orange: 'from-orange-500/20 to-orange-500/5 border-orange-500/20 hover:border-orange-500/40',
              }
              const textColorMap: Record<string, string> = {
                purple: 'text-purple-400', cyan: 'text-cyan-400', pink: 'text-pink-400',
                green: 'text-green-400', blue: 'text-blue-400', orange: 'text-orange-400',
              }
              return (
                <StaggerItem key={i}>
                  <div className={`agent-card bg-gradient-to-br ${colorMap[agent.color]}`}>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{agent.icon}</span>
                        <div>
                          <h3 className="font-semibold text-white">{agent.name}</h3>
                          <p className={`text-xs ${textColorMap[agent.color]}`}>{agent.role}</p>
                        </div>
                      </div>
                      <span className="px-2 py-1 rounded-full text-xs bg-green-500/10 text-green-400 border border-green-500/20">
                        {agent.status}
                      </span>
                    </div>
                    <p className="text-sm text-slate-400 mb-4 leading-relaxed">{agent.desc}</p>
                    <div className="flex items-center justify-between pt-3 border-t border-white/5">
                      <span className="text-xs text-slate-500">{agent.tasks} tasks completed</span>
                      <Link href="/auth/register" className={`text-xs font-medium ${textColorMap[agent.color]} hover:underline`}>
                        Try Now →
                      </Link>
                    </div>
                  </div>
                </StaggerItem>
              )
            })}
          </StaggerContainer>
        </div>
      </section>

      {/* ========================== HOW IT WORKS ========================== */}
      <section className="relative py-24 sm:py-32 border-y border-white/5">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <ScrollReveal>
            <div className="text-center mb-16">
              <span className="text-sm font-medium text-pink-400 tracking-wider uppercase mb-3 block">How It Works</span>
              <h2 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                Three Steps to{' '}
                <span className="gradient-text">Supercharge</span> Your Dev
              </h2>
            </div>
          </ScrollReveal>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '01', title: 'Connect Your Project', desc: 'Link your repository or create a new workspace. OmniDev AI analyzes your codebase architecture instantly.', icon: '🔗' },
              { step: '02', title: 'Deploy AI Agents', desc: 'Choose from 6 specialized agents or let the platform auto-assign the best team for your task.', icon: '🤖' },
              { step: '03', title: 'Ship at Lightspeed', desc: 'Watch as agents generate, review, test, and deploy code. Approve changes and merge with one click.', icon: '🚀' },
            ].map((item, i) => (
              <ScrollReveal key={i} delay={i * 0.15}>
                <div className="text-center relative">
                  <div className="text-5xl mb-4">{item.icon}</div>
                  <span className="text-xs font-bold text-purple-400/60 tracking-widest uppercase mb-2 block">Step {item.step}</span>
                  <h3 className="text-xl font-semibold text-white mb-3">{item.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{item.desc}</p>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* ========================== PRICING SECTION ========================== */}
      <section id="pricing" className="relative py-24 sm:py-32">
        <div className="orb orb-pink w-[400px] h-[400px] top-0 right-1/4 animate-pulse-glow" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <ScrollReveal>
            <div className="text-center mb-16">
              <span className="text-sm font-medium text-purple-400 tracking-wider uppercase mb-3 block">Pricing</span>
              <h2 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                Simple, Transparent{' '}
                <span className="gradient-text">Pricing</span>
              </h2>
              <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                Start free. Scale as your team grows. No hidden fees.
              </p>
            </div>
          </ScrollReveal>

          <StaggerContainer className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto" staggerDelay={0.12}>
            {PRICES.map((plan, i) => (
              <StaggerItem key={i}>
                <div className={`pricing-card ${plan.featured ? 'featured' : ''} h-full flex flex-col`}>
                  {plan.featured && (
                    <div className="text-xs font-semibold text-purple-300 tracking-wider uppercase mb-4">Most Popular</div>
                  )}
                  <h3 className="text-xl font-bold text-white mb-1">{plan.name}</h3>
                  <p className="text-sm text-slate-400 mb-6">{plan.desc}</p>
                  <div className="mb-6">
                    <span className="text-4xl font-bold text-white">${plan.price}</span>
                    {plan.price !== '0' && <span className="text-slate-500">/month</span>}
                  </div>
                  <ul className="space-y-3 mb-8 flex-1">
                    {plan.features.map((f, j) => (
                      <li key={j} className="flex items-center gap-2 text-sm text-slate-300">
                        <svg className="w-4 h-4 text-purple-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        {f}
                      </li>
                    ))}
                  </ul>
                  <Link
                    href="/auth/register"
                    className={plan.featured ? 'btn-primary w-full justify-center' : 'btn-outline w-full justify-center'}
                  >
                    {plan.cta}
                  </Link>
                </div>
              </StaggerItem>
            ))}
          </StaggerContainer>
        </div>
      </section>

      {/* ========================== CTA SECTION ========================== */}
      <section className="relative py-24 sm:py-32">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <ScrollReveal>
            <div className="glass-strong rounded-3xl p-12 sm:p-16 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 via-transparent to-cyan-500/10" />
              <div className="relative z-10">
                <h2 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                  Ready to Build the{' '}
                  <span className="gradient-text">Future</span>?
                </h2>
                <p className="text-lg text-slate-400 mb-8 max-w-2xl mx-auto">
                  Join thousands of developers using OmniDev AI to ship code 10x faster with autonomous AI agents.
                </p>
                <div className="flex flex-wrap justify-center gap-4">
                  <Link href="/auth/register" className="btn-primary text-base">
                    Start Building for Free
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </Link>
                  <Link href="/auth/login" className="btn-outline text-base">
                    Sign In
                  </Link>
                </div>
              </div>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* ========================== FOOTER ========================== */}
      <footer className="border-t border-white/5 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            {/* Brand */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center text-white font-bold text-sm">O</div>
                <span className="text-lg font-bold text-white">OmniDev <span className="gradient-text">AI</span></span>
              </div>
              <p className="text-sm text-slate-500 leading-relaxed">Autonomous AI-powered development platform for the next generation of builders.</p>
            </div>

            {/* Product */}
            <div>
              <h4 className="text-sm font-semibold text-white mb-3">Product</h4>
              <ul className="space-y-2 text-sm text-slate-500">
                <li><Link href="/#features" className="hover:text-white transition">Features</Link></li>
                <li><Link href="/#agents" className="hover:text-white transition">AI Agents</Link></li>
                <li><Link href="/#pricing" className="hover:text-white transition">Pricing</Link></li>
                <li><a href="http://localhost:8000/api/v1/docs" target="_blank" rel="noopener noreferrer" className="hover:text-white transition">API Docs ↗</a></li>
              </ul>
            </div>

            {/* Company */}
            <div>
              <h4 className="text-sm font-semibold text-white mb-3">Company</h4>
              <ul className="space-y-2 text-sm text-slate-500">
                <li><Link href="/about" className="hover:text-white transition">About</Link></li>
                <li><Link href="/blog" className="hover:text-white transition">Blog</Link></li>
                <li><Link href="/careers" className="hover:text-white transition">Careers</Link></li>
                <li><Link href="/contact" className="hover:text-white transition">Contact</Link></li>
              </ul>
            </div>

            {/* Legal */}
            <div>
              <h4 className="text-sm font-semibold text-white mb-3">Legal</h4>
              <ul className="space-y-2 text-sm text-slate-500">
                <li><Link href="/privacy" className="hover:text-white transition">Privacy</Link></li>
                <li><Link href="/terms" className="hover:text-white transition">Terms</Link></li>
                <li><Link href="/security" className="hover:text-white transition">Security</Link></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-white/5 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-slate-600">&copy; {new Date().getFullYear()} OmniDev AI. All rights reserved.</p>
            <div className="flex gap-4">
              <a href="https://github.com/Amank326/OmniDev-AI-Autonomous-Universal-Developer-Agent" target="_blank" rel="noopener noreferrer" className="text-sm text-slate-600 hover:text-white transition">GitHub</a>
              <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="text-sm text-slate-600 hover:text-white transition">Twitter</a>
              <a href="https://discord.com" target="_blank" rel="noopener noreferrer" className="text-sm text-slate-600 hover:text-white transition">Discord</a>
            </div>
          </div>
        </div>
      </footer>
    </>
  )
}
