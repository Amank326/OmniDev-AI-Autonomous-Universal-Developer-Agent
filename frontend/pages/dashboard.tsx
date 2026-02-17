import { useEffect, useState } from 'react'
import Head from 'next/head'
import Link from 'next/link'
import { useRouter } from 'next/router'
import Cookies from 'js-cookie'
import { authAPI, agentsAPI, notificationsAPI } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import Layout from '@/components/Layout'
import toast from 'react-hot-toast'
import { motion, AnimatePresence } from 'framer-motion'

interface User {
  id: number
  email: string
  username: string
  full_name: string | null
  role: string
}

interface Agent {
  id: number
  name: string
  agent_type: string
  status: string
}

interface Notification {
  id: number
  title: string
  message: string
  is_read: boolean
  created_at: string
}

const AGENT_TYPES = [
  { value: 'code_generator', label: 'CodeGen Agent', icon: '⚡', color: 'purple', desc: 'Generates production-ready code' },
  { value: 'code_reviewer', label: 'Review Agent', icon: '🔍', color: 'cyan', desc: 'Deep code review & security audit' },
  { value: 'documentation', label: 'Doc Agent', icon: '📝', color: 'pink', desc: 'Auto-generates documentation' },
  { value: 'debugger', label: 'Debug Agent', icon: '🐛', color: 'green', desc: 'Intelligent error tracing & fix' },
  { value: 'refactorer', label: 'Refactor Agent', icon: '🔄', color: 'blue', desc: 'Code restructuring & optimization' },
  { value: 'deployer', label: 'Deploy Agent', icon: '🚀', color: 'orange', desc: 'CI/CD & deployment automation' },
]

export default function Dashboard() {
  const router = useRouter()
  const { logout } = useAuth()
  const [user, setUser] = useState<User | null>(null)
  const [agents, setAgents] = useState<Agent[]>([])
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateAgent, setShowCreateAgent] = useState(false)
  const [newAgent, setNewAgent] = useState({ name: '', agent_type: 'code_generator', description: '' })
  const [creating, setCreating] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'agents' | 'notifications'>('overview')

  useEffect(() => {
    const token = Cookies.get('auth_token')
    if (!token) {
      router.push('/auth/login')
      return
    }

    Promise.all([
      authAPI.me().catch(() => null),
      agentsAPI.list().catch(() => null),
      notificationsAPI.list(true).catch(() => null),
    ])
      .then(([userRes, agentsRes, notifRes]) => {
        if (!userRes) {
          router.push('/auth/login')
          return
        }
        setUser(userRes.data)
        if (agentsRes) setAgents(agentsRes.data || [])
        if (notifRes) setNotifications(notifRes.data || [])
      })
      .finally(() => setLoading(false))
  }, [router])

  const handleCreateAgent = async () => {
    if (!newAgent.name.trim()) {
      toast.error('Agent name is required')
      return
    }
    setCreating(true)
    try {
      const res = await agentsAPI.create({
        name: newAgent.name,
        agent_type: newAgent.agent_type,
        description: newAgent.description || undefined,
      })
      setAgents((prev) => [...prev, res.data])
      setShowCreateAgent(false)
      setNewAgent({ name: '', agent_type: 'code_generator', description: '' })
      toast.success('Agent created successfully!')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create agent')
    } finally {
      setCreating(false)
    }
  }

  const handleDeleteAgent = async (agentId: number, agentName: string) => {
    if (!confirm(`Delete agent "${agentName}"? This cannot be undone.`)) return
    try {
      await agentsAPI.delete(agentId)
      setAgents((prev) => prev.filter((a) => a.id !== agentId))
      toast.success(`${agentName} deleted`)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete agent')
    }
  }

  const handleRunAgent = async (agent: Agent) => {
    try {
      toast.loading(`Running ${agent.name}...`, { id: `run-${agent.id}` })
      await agentsAPI.createTask(agent.id, {
        task_name: `${agent.agent_type}_run_${Date.now()}`,
        input_data: { source: 'dashboard', triggered_by: user?.username },
      })
      toast.success(`${agent.name} task started!`, { id: `run-${agent.id}` })
    } catch (error: any) {
      toast.error(error.response?.data?.detail || `Failed to run ${agent.name}`, { id: `run-${agent.id}` })
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-950">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full border-2 border-purple-500/30 border-t-purple-500 animate-spin" />
          <span className="text-sm text-slate-500">Loading dashboard...</span>
        </div>
      </div>
    )
  }

  const statusColor = (s: string) =>
    s === 'active' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
    s === 'running' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' :
    'bg-slate-500/10 text-slate-400 border-slate-500/20'

  const agentTypeInfo = (type: string) => AGENT_TYPES.find(t => t.value === type) || AGENT_TYPES[0]

  return (
    <Layout>
      <Head>
        <title>Dashboard — OmniDev AI</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
      </Head>

      <div className="max-w-7xl mx-auto px-4 pt-24 pb-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4"
        >
          <div>
            <h1 className="text-3xl font-bold text-white">
              Welcome back, <span className="gradient-text">{user?.full_name || user?.username}</span>
            </h1>
            <p className="text-slate-400 mt-1">Manage your AI agents and monitor activity</p>
          </div>
          <div className="flex items-center gap-3">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowCreateAgent(true)}
              className="btn-primary !py-2.5 !px-5 !text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
              New Agent
            </motion.button>
            <button
              onClick={logout}
              className="py-2.5 px-4 text-sm rounded-xl border border-white/10 text-slate-400 hover:text-red-400 hover:border-red-500/30 hover:bg-red-500/5 transition-all duration-300"
            >
              Logout
            </button>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
        >
          {[
            { label: 'Total Agents', value: agents.length, icon: '🤖', color: 'from-purple-500/20 to-purple-500/5', textColor: 'text-purple-400' },
            { label: 'Active Agents', value: agents.filter(a => a.status === 'active').length, icon: '✅', color: 'from-green-500/20 to-green-500/5', textColor: 'text-green-400' },
            { label: 'Notifications', value: notifications.length, icon: '🔔', color: 'from-cyan-500/20 to-cyan-500/5', textColor: 'text-cyan-400' },
            { label: 'Account', value: user?.role === 'admin' ? 'Admin' : 'Pro', icon: '👤', color: 'from-pink-500/20 to-pink-500/5', textColor: 'text-pink-400' },
          ].map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + i * 0.05 }}
              className="dash-card"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl">{stat.icon}</span>
                <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${stat.color}`} />
              </div>
              <p className={`text-2xl font-bold ${stat.textColor}`}>{stat.value}</p>
              <p className="text-xs text-slate-500 mt-1">{stat.label}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 p-1 glass rounded-xl w-fit">
          {(['overview', 'agents', 'notifications'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 capitalize ${
                activeTab === tab
                  ? 'bg-purple-500/20 text-purple-300 shadow-lg shadow-purple-500/10'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          {activeTab === 'overview' && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="grid lg:grid-cols-3 gap-6"
            >
              {/* Recent Agents */}
              <div className="lg:col-span-2 dash-card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-white">Recent Agents</h2>
                  <button onClick={() => setActiveTab('agents')} className="text-xs text-purple-400 hover:text-purple-300 transition">View all →</button>
                </div>
                {agents.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-4xl mb-4">🤖</div>
                    <p className="text-slate-400 mb-4">No agents yet. Create your first one!</p>
                    <button onClick={() => setShowCreateAgent(true)} className="text-sm text-purple-400 hover:text-purple-300 font-medium transition">
                      + Create Agent
                    </button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {agents.slice(0, 4).map((agent) => {
                      const info = agentTypeInfo(agent.agent_type)
                      return (
                        <div key={agent.id} className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5 hover:border-white/10 transition-all">
                          <div className="flex items-center gap-3">
                            <span className="text-xl">{info.icon}</span>
                            <div>
                              <h4 className="font-medium text-white text-sm">{agent.name}</h4>
                              <span className="text-xs text-slate-500">{info.label}</span>
                            </div>
                          </div>
                          <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${statusColor(agent.status)}`}>
                            {agent.status}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>

              {/* Notifications */}
              <div className="dash-card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-white">Notifications</h2>
                  {notifications.length > 0 && (
                    <button
                      onClick={async () => {
                        try {
                          await notificationsAPI.markAllRead()
                          setNotifications([])
                          toast.success('All marked as read')
                        } catch { toast.error('Failed') }
                      }}
                      className="text-xs text-slate-500 hover:text-white transition"
                    >
                      Clear all
                    </button>
                  )}
                </div>
                {notifications.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-3xl mb-2">🔕</div>
                    <p className="text-sm text-slate-500">All caught up!</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {notifications.slice(0, 5).map((n) => (
                      <div key={n.id} className="p-3 rounded-xl bg-purple-500/5 border border-purple-500/10">
                        <h4 className="text-sm font-medium text-white">{n.title}</h4>
                        <p className="text-xs text-slate-400 mt-1 line-clamp-2">{n.message}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {activeTab === 'agents' && (
            <motion.div
              key="agents"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {agents.length === 0 ? (
                  <div className="col-span-full text-center py-16">
                    <div className="text-5xl mb-4">🤖</div>
                    <p className="text-slate-400 mb-6 text-lg">No agents created yet</p>
                    <button onClick={() => setShowCreateAgent(true)} className="btn-primary">
                      Create Your First Agent
                    </button>
                  </div>
                ) : (
                  agents.map((agent) => {
                    const info = agentTypeInfo(agent.agent_type)
                    return (
                      <motion.div
                        key={agent.id}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="agent-card"
                      >
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-2xl">{info.icon}</span>
                          <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${statusColor(agent.status)}`}>
                            {agent.status}
                          </span>
                        </div>
                        <h3 className="font-semibold text-white mb-1">{agent.name}</h3>
                        <p className="text-xs text-slate-500 mb-3">{info.desc}</p>
                        <div className="flex items-center justify-between pt-3 border-t border-white/5">
                          <button
                            onClick={() => handleDeleteAgent(agent.id, agent.name)}
                            className="text-xs text-slate-600 hover:text-red-400 transition"
                          >
                            Delete
                          </button>
                          <button
                            onClick={() => handleRunAgent(agent)}
                            className="text-xs text-purple-400 hover:text-purple-300 font-medium"
                          >
                            Run →
                          </button>
                        </div>
                      </motion.div>
                    )
                  })
                )}
              </div>
            </motion.div>
          )}

          {activeTab === 'notifications' && (
            <motion.div
              key="notifications"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="dash-card"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-white">All Notifications</h2>
                {notifications.length > 0 && (
                  <button
                    onClick={async () => {
                      try {
                        await notificationsAPI.markAllRead()
                        setNotifications([])
                        toast.success('All marked as read')
                      } catch { toast.error('Failed') }
                    }}
                    className="text-xs text-purple-400 hover:text-purple-300 font-medium"
                  >
                    Mark All Read
                  </button>
                )}
              </div>
              {notifications.length === 0 ? (
                <div className="text-center py-16">
                  <div className="text-5xl mb-4">🔕</div>
                  <p className="text-slate-400 text-lg">No unread notifications</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {notifications.map((n) => (
                    <div key={n.id} className="flex items-start gap-3 p-4 rounded-xl bg-white/[0.02] border border-white/5 hover:border-purple-500/20 transition-all">
                      <div className="w-2 h-2 rounded-full bg-purple-400 mt-2 flex-shrink-0" />
                      <div>
                        <h4 className="font-medium text-white text-sm">{n.title}</h4>
                        <p className="text-sm text-slate-400 mt-1">{n.message}</p>
                        <p className="text-xs text-slate-600 mt-2">{new Date(n.created_at).toLocaleString()}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Create Agent Modal */}
      <AnimatePresence>
        {showCreateAgent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center"
            onClick={() => setShowCreateAgent(false)}
          >
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="relative z-10 w-full max-w-lg mx-4 glass-strong rounded-2xl p-6 sm:p-8"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-white">Create New Agent</h2>
                <button onClick={() => setShowCreateAgent(false)} className="text-slate-400 hover:text-white transition">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">Agent Name</label>
                  <input
                    type="text"
                    className="input-dark"
                    placeholder="My CodeGen Agent"
                    value={newAgent.name}
                    onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">Agent Type</label>
                  <div className="grid grid-cols-2 gap-2">
                    {AGENT_TYPES.map((type) => (
                      <button
                        key={type.value}
                        onClick={() => setNewAgent({ ...newAgent, agent_type: type.value })}
                        className={`p-3 rounded-xl border text-left transition-all ${
                          newAgent.agent_type === type.value
                            ? 'border-purple-500/40 bg-purple-500/10'
                            : 'border-white/5 bg-white/[0.02] hover:border-white/10'
                        }`}
                      >
                        <span className="text-lg">{type.icon}</span>
                        <p className="text-sm font-medium text-white mt-1">{type.label}</p>
                        <p className="text-xs text-slate-500">{type.desc}</p>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">Description (optional)</label>
                  <textarea
                    className="input-dark min-h-[80px] resize-none"
                    placeholder="Describe what this agent should do..."
                    value={newAgent.description}
                    onChange={(e) => setNewAgent({ ...newAgent, description: e.target.value })}
                  />
                </div>

                <div className="flex gap-3 pt-2">
                  <button onClick={() => setShowCreateAgent(false)} className="btn-outline flex-1 justify-center !py-3">
                    Cancel
                  </button>
                  <motion.button
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                    onClick={handleCreateAgent}
                    disabled={creating}
                    className="btn-primary flex-1 justify-center !py-3 disabled:opacity-50"
                  >
                    {creating ? (
                      <div className="flex items-center gap-2">
                        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                        Creating...
                      </div>
                    ) : 'Create Agent'}
                  </motion.button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </Layout>
  )
}
