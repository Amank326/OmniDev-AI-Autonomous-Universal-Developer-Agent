'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { LogOut, Plus, Zap, Code2, Gauge, Users } from 'lucide-react';
import apiClient from '@/lib/api';
import { useAuthStore } from '@/store/auth';
import { WebSocketStatus } from '@/components/WebSocketStatus';

interface Stats {
  total_projects: number;
  total_tasks: number;
  active_agents: number;
  completed_tasks: number;
}

export default function Dashboard() {
  const { isAuthenticated } = useAuth();
  const { user, logout } = useAuthStore();
  const [stats, setStats] = useState<Stats>({
    total_projects: 0,
    total_tasks: 0,
    active_agents: 0,
    completed_tasks: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await apiClient.get('/api/stats');
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      fetchStats();
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-black">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-800/50 backdrop-blur-lg sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Zap className="w-8 h-8 text-blue-400" />
            <span className="text-xl font-bold">OmniDev AI</span>
          </div>
          <div className="flex items-center gap-6">
            <span className="text-sm text-slate-300">{user?.email}</span>
            <button
              onClick={() => {
                logout();
              }}
              className="flex items-center gap-2 px-4 py-2 text-slate-300 hover:bg-slate-700 rounded-lg transition"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Welcome */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold mb-2">Welcome, {user?.full_name || user?.username}!</h1>
          <p className="text-slate-400">Manage your AI projects and agents</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {[
            {
              icon: Code2,
              label: 'Projects',
              value: stats.total_projects,
              color: 'from-blue-600 to-blue-400',
            },
            {
              icon: Gauge,
              label: 'Tasks',
              value: stats.total_tasks,
              color: 'from-purple-600 to-purple-400',
            },
            {
              icon: Zap,
              label: 'Active Agents',
              value: stats.active_agents,
              color: 'from-pink-600 to-pink-400',
            },
            {
              icon: Users,
              label: 'Completed',
              value: stats.completed_tasks,
              color: 'from-green-600 to-green-400',
            },
          ].map((stat, i) => (
            <div
              key={i}
              className={`p-6 rounded-xl bg-gradient-to-br ${stat.color} bg-opacity-10 border border-slate-700 hover:border-slate-600 transition`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">{stat.label}</p>
                  <p className="text-3xl font-bold mt-2">{loading ? '-' : stat.value}</p>
                </div>
                <stat.icon className="w-8 h-8 opacity-50" />
              </div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          <Link
            href="/projects/new"
            className="p-8 rounded-xl bg-slate-800/50 border border-slate-700 hover:border-blue-500 transition group cursor-pointer"
          >
            <Plus className="w-8 h-8 text-blue-400 mb-3 group-hover:scale-110 transition" />
            <h3 className="text-lg font-semibold mb-2">Create Project</h3>
            <p className="text-slate-400">Start a new AI project</p>
          </Link>

          <Link
            href="/agents"
            className="p-8 rounded-xl bg-slate-800/50 border border-slate-700 hover:border-purple-500 transition group cursor-pointer"
          >
            <Zap className="w-8 h-8 text-purple-400 mb-3 group-hover:scale-110 transition" />
            <h3 className="text-lg font-semibold mb-2">Deploy Agents</h3>
            <p className="text-slate-400">Manage AI agents and workflows</p>
          </Link>
        </div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 rounded-xl bg-slate-800/50 border border-slate-700 p-6">
            <h2 className="text-xl font-bold mb-4">Recent Activity</h2>
            <div className="space-y-4">
              <p className="text-slate-400 text-center py-8">No recent activity. Create a project to get started!</p>
            </div>
          </div>

          {/* WebSocket Status Sidebar */}
          <div>
            <WebSocketStatus showDetails={true} />
          </div>
        </div>
      </main>
    </div>
  );
}
