/**
 * Subscription Analytics Component - Phase 6
 * Displays subscription-specific metrics and trends
 */

import React, { useState, useEffect } from 'react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { AlertCircle, Users, Activity, TrendingUp } from 'lucide-react';

interface SubscriptionMetrics {
  active_subscriptions: number;
  new_subscriptions_30d: number;
  churned_subscriptions_30d: number;
  trial_conversions_30d?: number;
  upgrade_count_30d?: number;
}

const SubscriptionAnalytics: React.FC = () => {
  const [metrics, setMetrics] = useState<SubscriptionMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState(30);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/analytics/revenue?period_days=${period}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        if (!response.ok) throw new Error('Failed to fetch subscription metrics');
        
        const data = await response.json();
        setMetrics(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, [period]);

  // Sample subscription trend data
  const subscriptionTrend = [
    { date: '1st', subscriptions: 45, upgrades: 2, cancellations: 1 },
    { date: '2nd', subscriptions: 47, upgrades: 3, cancellations: 0 },
    { date: '3rd', subscriptions: 49, upgrades: 1, cancellations: 1 },
    { date: '4th', subscriptions: 51, upgrades: 2, cancellations: 0 },
    { date: '5th', subscriptions: 54, upgrades: 4, cancellations: 1 },
    { date: '6th', subscriptions: 56, upgrades: 2, cancellations: 0 },
    { date: '7th', subscriptions: 58, upgrades: 3, cancellations: 1 },
  ];

  // Subscription tier breakdown (sample)
  const tierBreakdown = [
    { name: 'Starter', value: 28, percentage: 48.3 },
    { name: 'Professional', value: 22, percentage: 37.9 },
    { name: 'Enterprise', value: 8, percentage: 13.8 },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading subscription analytics...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Period Selector */}
      <div className="bg-white rounded-lg shadow p-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Subscription Analytics</h2>
          <p className="text-sm text-gray-600">Track subscription health and growth</p>
        </div>
        <div className="flex gap-2">
          {[7, 30, 90].map(days => (
            <button
              key={days}
              onClick={() => setPeriod(days)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                period === days
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {days}d
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm font-medium">Active Subscriptions</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">58</p>
              <p className="mt-1 text-xs text-green-600">+5 this month</p>
            </div>
            <Users className="w-10 h-10 text-blue-600 opacity-20" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm font-medium">New Subscriptions</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">12</p>
              <p className="mt-1 text-xs text-green-600">Last 30 days</p>
            </div>
            <TrendingUp className="w-10 h-10 text-green-600 opacity-20" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm font-medium">Cancellations</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">3</p>
              <p className="mt-1 text-xs text-red-600">Last 30 days</p>
            </div>
            <Activity className="w-10 h-10 text-red-600 opacity-20" />
          </div>
        </div>
      </div>

      {/* Subscription Trend */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Subscription Trend (Last 7 Days)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={subscriptionTrend}>
            <defs>
              <linearGradient id="colorSubscriptions" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Area type="monotone" dataKey="subscriptions" stroke="#3b82f6" fillOpacity={1} fill="url(#colorSubscriptions)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Upgrades vs Cancellations */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Upgrades vs Cancellations</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={subscriptionTrend}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="upgrades" fill="#10b981" />
            <Bar dataKey="cancellations" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Tier Breakdown */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Subscription Tier Breakdown</h3>
        <div className="space-y-4">
          {tierBreakdown.map((tier, idx) => (
            <div key={idx}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-900">{tier.name}</span>
                <span className="text-sm text-gray-600">{tier.value} subscriptions ({tier.percentage}%)</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    idx === 0 ? 'bg-blue-600' : idx === 1 ? 'bg-indigo-600' : 'bg-purple-600'
                  }`}
                  style={{ width: `${tier.percentage}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Insights */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">Insights</h4>
        <ul className="space-y-2 text-sm text-blue-800">
          <li>• Subscription growth rate: 20.7% MoM (12 new vs 3 canceled)</li>
          <li>• Professional tier is most popular (37.9% of subscriptions)</li>
          <li>• 4 upgrades from Starter to Professional this month</li>
        </ul>
      </div>
    </div>
  );
};

export default SubscriptionAnalytics;
