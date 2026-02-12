/**
 * Customer Analytics Component - Phase 6
 * Displays customer cohort analysis, churn prediction, and insights
 */

import React, { useState, useEffect } from 'react';
import { LineChart, Line, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { AlertCircle, BarChart3, TrendingDown, Users, Heart } from 'lucide-react';

interface CustomerMetrics {
  total_customers: number;
  new_customers_30d: number;
  churn_risk_high: number;
  avg_health_score: number;
}

const CustomerAnalytics: React.FC = () => {
  const [metrics, setMetrics] = useState<CustomerMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCohort, setSelectedCohort] = useState('2024-12');
  const [riskLevel, setRiskLevel] = useState('all');

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/analytics/customers', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        if (!response.ok) throw new Error('Failed to fetch customer metrics');
        
        const data = await response.json();
        setMetrics(data);
      } catch (err) {
        console.error('Error fetching metrics:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  // Sample cohort retention data
  const cohortData = {
    '2024-12': [100, 92, 85, 78, 71],
    '2024-11': [100, 88, 79, 70],
    '2024-10': [100, 85, 73],
  };

  // Sample customer churn risk distribution
  const churnRiskData = [
    { range: '0-10%', customers: 38, percentage: 65.5 },
    { range: '10-30%', customers: 14, percentage: 24.1 },
    { range: '30-50%', customers: 5, percentage: 8.6 },
    { range: '50%+', customers: 1, percentage: 1.7 },
  ];

  // Sample customer health distribution
  const healthData = [
    { score: 90, customers: 35 },
    { score: 80, customers: 18 },
    { score: 70, customers: 10 },
    { score: 60, customers: 3 },
    { score: 50, customers: 2 },
  ];

  // Sample customer lifetime value by cohort
  const ltvByCohort = [
    { month: '2024-10', avg_ltv: 245 },
    { month: '2024-11', avg_ltv: 287 },
    { month: '2024-12', avg_ltv: 312 },
    { month: '2025-01', avg_ltv: 298 },
    { month: '2025-02', avg_ltv: 321 },
  ];

  // High risk customers (sample)
  const highRiskCustomers = [
    { id: 'cust_001', name: 'Acme Corp', risk: 0.75, health: 35, days_inactive: 45 },
    { id: 'cust_002', name: 'Tech Startup Inc', risk: 0.68, health: 42, days_inactive: 38 },
    { id: 'cust_003', name: 'Growth Industries', risk: 0.62, health: 48, days_inactive: 32 },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading customer analytics...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold text-gray-900">Customer Analytics</h2>
        <p className="text-sm text-gray-600">Cohort analysis, churn prediction, and customer health</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm font-medium">Total Customers</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">58</p>
            </div>
            <Users className="w-10 h-10 text-blue-600 opacity-20" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm font-medium">New Customers (30d)</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">7</p>
            </div>
            <BarChart3 className="w-10 h-10 text-green-600 opacity-20" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm font-medium">High Risk</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">3</p>
              <p className="mt-1 text-xs text-red-600">Churn risk > 60%</p>
            </div>
            <AlertCircle className="w-10 h-10 text-red-600 opacity-20" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm font-medium">Avg Health Score</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">77</p>
              <p className="mt-1 text-xs text-green-600">Above average</p>
            </div>
            <Heart className="w-10 h-10 text-pink-600 opacity-20" />
          </div>
        </div>
      </div>

      {/* Cohort Retention Analysis */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Cohort Retention Analysis</h3>
        
        {/* Cohort Selector */}
        <div className="mb-4 flex gap-2">
          {Object.keys(cohortData).map(month => (
            <button
              key={month}
              onClick={() => setSelectedCohort(month)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                selectedCohort === month
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {month}
            </button>
          ))}
        </div>

        {/* Cohort Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 border-t border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-900">Cohort Month</th>
                {[0, 1, 2, 3, 4].map(i => (
                  <th key={i} className="px-4 py-3 text-center font-medium text-gray-900">
                    Month {i}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.entries(cohortData).map(([month, retention], idx) => (
                <tr key={month} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-4 py-3 font-medium text-gray-900">{month}</td>
                  {retention.map((rate, i) => (
                    <td key={i} className="px-4 py-3 text-center">
                      <div className="inline-block px-3 py-1 rounded font-medium" style={{
                        backgroundColor: `rgba(16, 185, 129, ${rate / 100 * 0.3})`,
                        color: rate >= 80 ? '#059669' : rate >= 60 ? '#f59e0b' : '#ef4444'
                      }}>
                        {rate}%
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Customer Health Distribution */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Customer Health Score Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="score" name="Health Score" domain={[0, 100]} />
            <YAxis dataKey="customers" name="Number of Customers" />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
            <Scatter name="Customers" data={healthData} fill="#3b82f6" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* LTV by Cohort */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Average LTV by Cohort</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={ltvByCohort}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip formatter={(value) => `$${value}`} />
            <Legend />
            <Line type="monotone" dataKey="avg_ltv" stroke="#3b82f6" strokeWidth={2} dot={{ fill: '#3b82f6' }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Churn Risk Distribution */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Churn Risk Distribution</h3>
        <div className="space-y-4">
          {churnRiskData.map((item, idx) => (
            <div key={idx}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-900">{item.range}</span>
                <span className="text-sm text-gray-600">{item.customers} customers ({item.percentage}%)</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    item.range === '0-10%' ? 'bg-green-600' :
                    item.range === '10-30%' ? 'bg-yellow-600' :
                    item.range === '30-50%' ? 'bg-orange-600' : 'bg-red-600'
                  }`}
                  style={{ width: `${item.percentage}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* High Risk Customers */}
      <div className="bg-red-50 rounded-lg shadow p-6 border border-red-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-red-900">High Risk Customers</h3>
          <span className="text-sm font-medium text-red-600">Action Required</span>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="border-b border-red-300">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-red-900">Customer</th>
                <th className="px-4 py-2 text-center font-medium text-red-900">Churn Risk</th>
                <th className="px-4 py-2 text-center font-medium text-red-900">Health</th>
                <th className="px-4 py-2 text-center font-medium text-red-900">Inactive Days</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-200">
              {highRiskCustomers.map((customer, idx) => (
                <tr key={idx} className="bg-white hover:bg-red-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{customer.name}</td>
                  <td className="px-4 py-3 text-center">
                    <span className="inline-block px-2 py-1 rounded text-sm font-semibold bg-red-200 text-red-800">
                      {(customer.risk * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center text-red-600 font-medium">{customer.health}</td>
                  <td className="px-4 py-3 text-center text-gray-600">{customer.days_inactive}d</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2 justify-end">
        <button className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
          Download Report
        </button>
        <button className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700">
          Contact At-Risk Customers
        </button>
      </div>
    </div>
  );
};

export default CustomerAnalytics;
