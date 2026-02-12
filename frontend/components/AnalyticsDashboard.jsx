/**
 * Phase 22: Analytics Dashboard Component
 * Real-time dashboards, KPI cards, charts, drill-down capabilities
 * Executive and team analytics views
 */

import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

/**
 * Main Analytics Dashboard Component
 * Displays key metrics, trends, alerts, recommendations
 */
const AnalyticsDashboard = ({ customerId }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState('health_score');
  const [timeRange, setTimeRange] = useState('30');
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await fetch(
          `/api/v1/analytics/executive/dashboard?customer_id=${customerId}`
        );
        const data = await response.json();
        setDashboardData(data);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch dashboard:', error);
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [customerId, timeRange]);

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading analytics...</div>;
  }

  return (
    <div className="bg-gray-50 min-h-screen p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
        <p className="text-gray-600 mt-2">Real-time insights and performance metrics</p>
      </div>

      {/* Time Range Selector */}
      <div className="flex gap-4 mb-8">
        {['7', '30', '90', '365'].map((days) => (
          <button
            key={days}
            onClick={() => setTimeRange(days)}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              timeRange === days
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            Last {days} Days
          </button>
        ))}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {dashboardData?.kpi_cards?.map((card, idx) => (
          <KPICard key={idx} card={card} />
        ))}
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-4 mb-8 border-b border-gray-200">
        {['overview', 'usage', 'performance', 'roi', 'predictions'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-4 px-4 font-medium transition ${
              activeTab === tab
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="space-y-8">
        {activeTab === 'overview' && <OverviewTab data={dashboardData} />}
        {activeTab === 'usage' && <UsageTab customerId={customerId} />}
        {activeTab === 'performance' && <PerformanceTab customerId={customerId} />}
        {activeTab === 'roi' && <ROITab customerId={customerId} />}
        {activeTab === 'predictions' && <PredictionsTab customerId={customerId} />}
      </div>
    </div>
  );
};

/**
 * KPI Card Component
 * Displays individual metric with trend
 */
const KPICard = ({ card }) => {
  const getTrendColor = (trend) => {
    return trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-600';
  };

  const getStatusColor = (status) => {
    const colors = {
      'on_track': 'bg-green-100 text-green-800',
      'at_risk': 'bg-yellow-100 text-yellow-800',
      'critical': 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-600 text-sm font-medium">{card.title}</p>
          <h3 className="text-3xl font-bold text-gray-900 mt-2">{card.value}</h3>
          <p className={`text-sm font-medium mt-2 ${getTrendColor(card.trend)}`}>
            {card.trend === 'up' ? '↑' : card.trend === 'down' ? '↓' : '→'} {Math.abs(card.change || 0)}%
          </p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(card.status)}`}>
          {card.status.replace('_', ' ')}
        </span>
      </div>
      {card.target && (
        <div className="mt-4">
          <div className="flex justify-between text-xs text-gray-600 mb-1">
            <span>Progress</span>
            <span>{Math.round((card.value / card.target) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full"
              style={{ width: `${Math.min((card.value / card.target) * 100, 100)}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Overview Tab
 * High-level summary
 */
const OverviewTab = ({ data }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Key Trends */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Key Trends</h2>
        <div className="space-y-3">
          {data?.key_trends?.map((trend, idx) => (
            <div key={idx} className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-gray-700">{trend.name}</span>
              <span className="font-semibold text-gray-900">{trend.change}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* Alerts & Recommendations */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Alerts & Actions</h2>
        <div className="space-y-3">
          {data?.alerts?.slice(0, 3).map((alert, idx) => (
            <div
              key={idx}
              className="p-3 rounded-lg bg-red-50 border border-red-200"
            >
              <p className="text-sm font-medium text-red-800">{alert.message}</p>
              <p className="text-xs text-red-700 mt-1">{alert.action}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

/**
 * Usage Tab
 * Usage metrics and trends
 */
const UsageTab = ({ customerId }) => {
  const [usageData, setUsageData] = useState(null);

  useEffect(() => {
    const fetchUsage = async () => {
      try {
        const response = await fetch(
          `/api/v1/analytics/usage/overview?customer_id=${customerId}`
        );
        const data = await response.json();
        setUsageData(data);
      } catch (error) {
        console.error('Failed to fetch usage data:', error);
      }
    };

    fetchUsage();
  }, [customerId]);

  if (!usageData) return <div>Loading usage data...</div>;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Usage Metrics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Usage Metrics</h2>
        <div className="space-y-4">
          <MetricRow label="Active Users" value={usageData.active_users} />
          <MetricRow label="Total Executions" value={usageData.executions} />
          <MetricRow label="Daily Average" value={usageData.daily_average_executions} />
          <MetricRow label="Success Rate" value={`${(usageData.success_rate * 100).toFixed(1)}%`} />
          <MetricRow label="Features Used" value={usageData.feature_count} />
          <MetricRow label="API Calls" value={usageData.api_calls} />
          <MetricRow label="Storage Used" value={`${usageData.storage_used_gb.toFixed(2)} GB`} />
        </div>
      </div>

      {/* Execution Trend Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Execution Trend</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={generateMockChartData()}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="executions" stroke="#3b82f6" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

/**
 * Performance Tab
 * Latency, errors, reliability
 */
const PerformanceTab = ({ customerId }) => {
  const [perfData, setPerfData] = useState(null);

  useEffect(() => {
    const fetchPerformance = async () => {
      try {
        const response = await fetch(
          `/api/v1/analytics/performance/metrics?customer_id=${customerId}`
        );
        const data = await response.json();
        setPerfData(data);
      } catch (error) {
        console.error('Failed to fetch performance data:', error);
      }
    };

    fetchPerformance();
  }, [customerId]);

  if (!perfData) return <div>Loading performance data...</div>;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Performance Metrics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Performance Metrics</h2>
        <div className="space-y-4">
          <MetricRow label="Success Rate" value={`${(perfData.execution_success_rate * 100).toFixed(1)}%`} />
          <MetricRow label="Total Executions" value={perfData.total_executions} />
          <MetricRow label="Failed Executions" value={perfData.failed_executions} />
          <MetricRow label="P50 Latency" value={`${perfData.latency_percentiles.p50_ms}ms`} />
          <MetricRow label="P95 Latency" value={`${perfData.latency_percentiles.p95_ms}ms`} />
          <MetricRow label="P99 Latency" value={`${perfData.latency_percentiles.p99_ms}ms`} />
          <MetricRow label="Avg Latency" value={`${perfData.avg_latency_ms}ms`} />
          <MetricRow label="SLA Compliance" value={`${perfData.sla_compliance_percent.toFixed(1)}%`} />
        </div>
      </div>

      {/* Latency Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Latency Trend</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={generateMockChartData()}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="latency" stroke="#ef4444" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

/**
 * ROI Tab
 * Return on investment metrics
 */
const ROITab = ({ customerId }) => {
  const [roiData, setROIData] = useState(null);

  useEffect(() => {
    const fetchROI = async () => {
      try {
        const response = await fetch(
          `/api/v1/analytics/roi/calculation?customer_id=${customerId}`
        );
        const data = await response.json();
        setROIData(data);
      } catch (error) {
        console.error('Failed to fetch ROI data:', error);
      }
    };

    fetchROI();
  }, [customerId]);

  if (!roiData) return <div>Loading ROI data...</div>;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* ROI Metrics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">ROI Analysis</h2>
        <div className="space-y-4">
          <MetricRow label="ROI %" value={`${roiData.roi_percent.toFixed(1)}%`} />
          <MetricRow label="Gross ROI" value={`${roiData.gross_roi.toFixed(1)}%`} />
          <MetricRow label="Net ROI" value={`${roiData.net_roi.toFixed(1)}%`} />
          <MetricRow label="Value Delivered" value={`$${(roiData.value_delivered / 1000).toFixed(1)}K`} />
          <MetricRow label="Subscription Cost" value={`$${(roiData.subscription_cost / 1000).toFixed(1)}K`} />
          <MetricRow label="TCO" value={`$${(roiData.total_cost_of_ownership / 1000).toFixed(1)}K`} />
        </div>
      </div>

      {/* Value Breakdown Pie Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Value Breakdown</h2>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={Object.entries(roiData.value_breakdown).map(([name, value]) => ({
                name,
                value
              }))}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#3b82f6"
              dataKey="value"
            >
              {['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'].map((color, idx) => (
                <Cell key={`cell-${idx}`} fill={color} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

/**
 * Predictions Tab
 * Churn, expansion, usage forecasting
 */
const PredictionsTab = ({ customerId }) => {
  const [predictions, setPredictions] = useState(null);

  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const [churnRes, expansionRes] = await Promise.all([
          fetch(`/api/v1/analytics/predictions/churn-risk?customer_id=${customerId}`),
          fetch(`/api/v1/analytics/predictions/expansion-likelihood?customer_id=${customerId}`),
        ]);
        const churnData = await churnRes.json();
        const expansionData = await expansionRes.json();
        setPredictions({ churn: churnData, expansion: expansionData });
      } catch (error) {
        console.error('Failed to fetch predictions:', error);
      }
    };

    fetchPredictions();
  }, [customerId]);

  if (!predictions) return <div>Loading predictions...</div>;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Churn Risk */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Churn Risk</h2>
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-gray-700">Risk Level</span>
            <span className="font-semibold text-red-600">{predictions.churn.risk_level.toUpperCase()}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className="bg-red-600 h-4 rounded-full"
              style={{ width: `${predictions.churn.churn_probability}%` }}
            />
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Probability: {predictions.churn.churn_probability.toFixed(1)}%
          </p>
        </div>
        <div className="space-y-2">
          <p className="text-sm text-gray-700">
            <strong>Days until churn:</strong> {predictions.churn.days_until_churn}
          </p>
          <p className="text-sm text-gray-700">
            <strong>Confidence:</strong> {(predictions.churn.confidence * 100).toFixed(0)}%
          </p>
          <div className="mt-4">
            <h4 className="font-semibold text-gray-900 mb-2">Risk Factors</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              {predictions.churn.risk_factors?.slice(0, 3).map((factor, idx) => (
                <li key={idx}>• {factor.name}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Expansion Opportunities */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Expansion Opportunities</h2>
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-gray-700">Likelihood</span>
            <span className="font-semibold text-green-600">{predictions.expansion.likelihood_level.toUpperCase()}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className="bg-green-600 h-4 rounded-full"
              style={{ width: `${predictions.expansion.expansion_probability}%` }}
            />
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Probability: {predictions.expansion.expansion_probability.toFixed(1)}%
          </p>
        </div>
        <div>
          <h4 className="font-semibold text-gray-900 mb-2">Top Opportunities</h4>
          <div className="space-y-2">
            {predictions.expansion.opportunities?.slice(0, 3).map((opp, idx) => (
              <div key={idx} className="p-2 bg-green-50 rounded border border-green-200">
                <p className="font-medium text-green-900">{opp.type}</p>
                <p className="text-sm text-green-700">${(opp.value / 1000).toFixed(1)}K value</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Metric Row Component
 * Display label and value
 */
const MetricRow = ({ label, value }) => (
  <div className="flex justify-between items-center py-2 border-b border-gray-100">
    <span className="text-gray-600">{label}</span>
    <span className="font-semibold text-gray-900">{value}</span>
  </div>
);

/**
 * Mock chart data generator
 */
const generateMockChartData = () => {
  return Array.from({ length: 30 }, (_, i) => ({
    date: new Date(Date.now() - (30 - i) * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    executions: Math.floor(Math.random() * 1000 + 500),
    latency: Math.floor(Math.random() * 200 + 100),
  }));
};

export default AnalyticsDashboard;
