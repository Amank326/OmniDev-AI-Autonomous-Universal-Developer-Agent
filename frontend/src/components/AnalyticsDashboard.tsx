/**
 * Analytics Dashboard - Phase 6
 * Main analytics dashboard component with key metrics
 */

import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AlertCircle, TrendingUp, TrendingDown, Users, DollarSign, Activity } from 'lucide-react';

interface MetricCard {
  title: string;
  value: string | number;
  currency?: string;
  trend?: number;
  icon: React.ReactNode;
  description?: string;
}

interface DashboardData {
  mrr: {
    value: number;
    subscription_count: number;
  };
  arr: {
    value: number;
  };
  ltv: {
    average_ltv: number;
    customer_count: number;
  };
  churn_rate: {
    value: number;
  };
  revenue_metrics: {
    new_revenue: number;
    churned_revenue: number;
    net_revenue: number;
  };
  customer_metrics: {
    total_customers: number;
    new_customers_30d: number;
    retention_rate: number;
  };
  forecast: Array<{
    date: string;
    predicted_value: number;
    confidence: number;
  }>;
}

const AnalyticsDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/analytics/dashboard', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        if (!response.ok) throw new Error('Failed to fetch dashboard data');
        
        const data = await response.json();
        setDashboardData(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
    const interval = setInterval(fetchDashboard, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
        <div>
          <h3 className="text-sm font-medium text-red-900">Error Loading Analytics</h3>
          <p className="text-sm text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return <div className="text-center text-gray-500">No data available</div>;
  }

  const metrics: MetricCard[] = [
    {
      title: 'Monthly Recurring Revenue',
      value: `$${dashboardData.mrr.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
      description: `${dashboardData.mrr.subscription_count} active subscriptions`,
      icon: <DollarSign className="w-8 h-8 text-green-600" />
    },
    {
      title: 'Annual Recurring Revenue',
      value: `$${dashboardData.arr.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
      icon: <TrendingUp className="w-8 h-8 text-blue-600" />
    },
    {
      title: 'Customer Lifetime Value',
      value: `$${dashboardData.ltv.average_ltv.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
      description: `Avg from ${dashboardData.ltv.customer_count} customers`,
      icon: <Users className="w-8 h-8 text-purple-600" />
    },
    {
      title: 'Churn Rate (30d)',
      value: `${dashboardData.churn_rate.value.toFixed(2)}%`,
      icon: <TrendingDown className="w-8 h-8 text-red-600" />
    },
    {
      title: 'Total Customers',
      value: dashboardData.customer_metrics.total_customers,
      description: `+${dashboardData.customer_metrics.new_customers_30d} this month`,
      icon: <Users className="w-8 h-8 text-indigo-600" />
    },
    {
      title: 'Retention Rate',
      value: `${dashboardData.customer_metrics.retention_rate.toFixed(1)}%`,
      icon: <Activity className="w-8 h-8 text-emerald-600" />
    }
  ];

  return (
    <div className="space-y-6">
      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {metrics.map((metric, index) => (
          <div key={index} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-gray-500 text-sm font-medium">{metric.title}</p>
                <p className="mt-2 text-3xl font-bold text-gray-900">{metric.value}</p>
                {metric.description && (
                  <p className="mt-1 text-xs text-gray-600">{metric.description}</p>
                )}
              </div>
              <div className="ml-4">{metric.icon}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Revenue Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue Breakdown (30d)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={[
              {
                name: 'Revenue Type',
                'New Revenue': dashboardData.revenue_metrics.new_revenue,
                'Churned': -dashboardData.revenue_metrics.churned_revenue,
                'Net': dashboardData.revenue_metrics.net_revenue
              }
            ]}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => `$${value}`} />
              <Legend />
              <Bar dataKey="New Revenue" fill="#10b981" />
              <Bar dataKey="Churned" fill="#ef4444" />
              <Bar dataKey="Net" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Revenue Forecast */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">MRR Forecast (30 days)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dashboardData.forecast.slice(0, 30).map(f => ({
              date: new Date(f.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
              MRR: f.predicted_value,
              confidence: f.confidence
            }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => `$${value}`} />
              <Legend />
              <Line type="monotone" dataKey="MRR" stroke="#3b82f6" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Customer Metrics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Customer Metrics Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="border-l-4 border-blue-500 pl-4">
            <p className="text-gray-600 text-sm">Total Customers</p>
            <p className="text-2xl font-bold text-gray-900">{dashboardData.customer_metrics.total_customers}</p>
          </div>
          <div className="border-l-4 border-green-500 pl-4">
            <p className="text-gray-600 text-sm">New Customers (30d)</p>
            <p className="text-2xl font-bold text-gray-900">+{dashboardData.customer_metrics.new_customers_30d}</p>
          </div>
          <div className="border-l-4 border-emerald-500 pl-4">
            <p className="text-gray-600 text-sm">Retention Rate</p>
            <p className="text-2xl font-bold text-gray-900">{dashboardData.customer_metrics.retention_rate.toFixed(1)}%</p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2 justify-end">
        <button className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
          Export Report
        </button>
        <button className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
          View Details
        </button>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
