import React, { useState, useEffect } from 'react';
import {
  TrendingUp, TrendingDown, AlertCircle, CheckCircle, Activity,
  Clock, DollarSign, Zap, BarChart3, LineChart, PieChart, AlertTriangle
} from 'lucide-react';
import '../styles/agent-monitor.css';

const AgentMonitor = () => {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [health, setHealth] = useState(null);
  const [costs, setCosts] = useState(null);
  const [errors, setErrors] = useState(null);
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState(30);

  useEffect(() => {
    fetchAgents();
  }, []);

  useEffect(() => {
    if (selectedAgent) {
      fetchAgentMetrics();
    }
  }, [selectedAgent, timeRange]);

  const fetchAgents = async () => {
    try {
      const response = await fetch('/api/v1/agents/search?limit=100&sort_by=downloads');
      const data = await response.json();
      setAgents(data.agents || []);
      if (data.agents?.length > 0) {
        setSelectedAgent(data.agents[0]);
      }
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  };

  const fetchAgentMetrics = async () => {
    if (!selectedAgent) return;

    setLoading(true);
    try {
      const [perfRes, healthRes, costsRes, errorsRes] = await Promise.all([
        fetch(`/api/v1/agents/${selectedAgent.id}/performance?days=${timeRange}`),
        fetch(`/api/v1/agents/${selectedAgent.id}/health`),
        fetch(`/api/v1/agents/${selectedAgent.id}/costs?days=${timeRange}`),
        fetch(`/api/v1/agents/${selectedAgent.id}/errors?days=${timeRange}`)
      ]);

      const [perfData, healthData, costsData, errorsData] = await Promise.all([
        perfRes.json(),
        healthRes.json(),
        costsRes.json(),
        errorsRes.json()
      ]);

      setPerformance(perfData);
      setHealth(healthData);
      setCosts(costsData);
      setErrors(errorsData);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const StatusBadge = ({ status }) => {
    const statusConfig = {
      healthy: { color: 'green', icon: CheckCircle, label: 'Healthy' },
      degraded: { color: 'orange', icon: AlertTriangle, label: 'Degraded' },
      unhealthy: { color: 'red', icon: AlertCircle, label: 'Unhealthy' },
      idle: { color: 'gray', icon: Activity, label: 'Idle' }
    };

    const config = statusConfig[status] || statusConfig.idle;
    const Icon = config.icon;

    return (
      <div className={`status-badge status-${config.color}`}>
        <Icon size={16} />
        <span>{config.label}</span>
      </div>
    );
  };

  const MetricCard = ({ icon: Icon, label, value, unit = '', trend = null }) => (
    <div className="metric-card">
      <div className="metric-icon">
        <Icon size={24} />
      </div>
      <div className="metric-content">
        <p className="metric-label">{label}</p>
        <p className="metric-value">
          {typeof value === 'number' ? value.toFixed(2) : value}
          {unit && <span className="metric-unit">{unit}</span>}
        </p>
        {trend && (
          <p className={`metric-trend ${trend > 0 ? 'positive' : 'negative'}`}>
            {trend > 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            {Math.abs(trend).toFixed(1)}%
          </p>
        )}
      </div>
    </div>
  );

  const PerformanceChart = () => {
    if (!performance?.daily_metrics) return null;

    return (
      <div className="chart-container">
        <h4>Performance Over Time</h4>
        <div className="chart-wrapper">
          <div className="simple-chart">
            {performance.daily_metrics.slice(-7).map((day, idx) => (
              <div key={idx} className="chart-bar">
                <div
                  className="bar"
                  style={{
                    height: `${(day.success_rate / 100) * 100}%`,
                    background: day.success_rate >= 95 ? '#10b981' : '#f59e0b'
                  }}
                  title={`${day.date}: ${day.success_rate.toFixed(1)}%`}
                />
                <span className="bar-label">{day.date.slice(-2)}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="chart-legend">
          <p>Success Rate (Last 7 Days)</p>
        </div>
      </div>
    );
  };

  const CostBreakdown = () => {
    if (!costs) return null;

    return (
      <div className="cost-breakdown">
        <h4>Cost Analytics</h4>
        <div className="cost-grid">
          <div className="cost-item">
            <label>Total Cost</label>
            <p className="cost-value">${costs.total_cost?.toFixed(2) || '0.00'}</p>
          </div>
          <div className="cost-item">
            <label>Cost per Execution</label>
            <p className="cost-value">${costs.cost_per_execution?.toFixed(4) || '0.00'}</p>
          </div>
          <div className="cost-item">
            <label>Total Tokens</label>
            <p className="cost-value">{(costs.total_tokens / 1000).toFixed(1)}K</p>
          </div>
          <div className="cost-item">
            <label>Trend</label>
            <p className={`cost-trend ${costs.cost_trend === 'increasing' ? 'up' : costs.cost_trend === 'decreasing' ? 'down' : 'stable'}`}>
              {costs.cost_trend === 'increasing' && '📈 Increasing'}
              {costs.cost_trend === 'decreasing' && '📉 Decreasing'}
              {costs.cost_trend === 'stable' && '➡️ Stable'}
            </p>
          </div>
        </div>
      </div>
    );
  };

  const ErrorAnalytics = () => {
    if (!errors || !errors.error_types) return null;

    return (
      <div className="error-analytics">
        <h4>Error Analysis</h4>
        <div className="error-stats">
          <div className="error-stat">
            <label>Total Errors</label>
            <p className="error-count">{errors.total_errors}</p>
          </div>
          <div className="error-stat">
            <label>Error Rate</label>
            <p className={`error-rate ${errors.error_rate > 10 ? 'high' : 'acceptable'}`}>
              {errors.error_rate.toFixed(2)}%
            </p>
          </div>
        </div>

        {errors.error_types?.length > 0 && (
          <div className="error-types">
            <h5>Error Types</h5>
            <div className="error-list">
              {errors.error_types.map((err, idx) => (
                <div key={idx} className="error-item">
                  <span className="error-type">{err.type}</span>
                  <span className="error-count">{err.count}</span>
                  <div className="error-bar">
                    <div
                      className="bar-fill"
                      style={{ width: `${err.percentage}%` }}
                    />
                  </div>
                  <span className="error-percentage">{err.percentage.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {errors.recent_errors?.length > 0 && (
          <div className="recent-errors">
            <h5>Recent Errors</h5>
            <div className="errors-log">
              {errors.recent_errors.map((err, idx) => (
                <div key={idx} className="error-log-item">
                  <span className="error-time">
                    {new Date(err.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="error-msg">{err.error_message}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const HealthHistory = () => {
    if (!health?.history) return null;

    return (
      <div className="health-history">
        <h4>Health Timeline</h4>
        <div className="timeline">
          {health.history?.slice(-7).map((entry, idx) => (
            <div key={idx} className="timeline-item">
              <div className={`timeline-dot status-${entry.status}`} />
              <div className="timeline-content">
                <p className="timeline-date">{entry.date}</p>
                <p className="timeline-stat">
                  {entry.executions} executions
                  {entry.success_rate && ` • ${entry.success_rate.toFixed(1)}% success`}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (!selectedAgent) {
    return <div className="agent-monitor loading">Loading agents...</div>;
  }

  return (
    <div className="agent-monitor">
      <header className="monitor-header">
        <h1>Agent Performance Monitor</h1>
        <p>Real-time metrics, health status, and analytics for your agents</p>
      </header>

      <div className="monitor-layout">
        {/* Agent Selector */}
        <aside className="agent-sidebar">
          <h3>Agents</h3>
          <div className="agent-list">
            {agents.map(agent => (
              <button
                key={agent.id}
                className={`agent-item ${selectedAgent?.id === agent.id ? 'active' : ''}`}
                onClick={() => setSelectedAgent(agent)}
              >
                <span className="agent-name">{agent.name}</span>
                <span className="agent-downloads">{(agent.downloads / 1000).toFixed(1)}K</span>
              </button>
            ))}
          </div>
        </aside>

        {/* Main Content */}
        <main className="monitor-content">
          {/* Agent Header */}
          <div className="agent-header-section">
            <div className="agent-info">
              <h2>{selectedAgent.name}</h2>
              <p>{selectedAgent.description}</p>
            </div>
            <div className="agent-controls">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(parseInt(e.target.value))}
                className="time-range-select"
              >
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
                <option value={365}>Last year</option>
              </select>
            </div>
          </div>

          {/* Health Status */}
          {health && (
            <div className="status-section">
              <StatusBadge status={health.status} />
              {health.last_execution && (
                <p className="last-execution">
                  Last execution: {new Date(health.last_execution).toLocaleTimeString()}
                </p>
              )}
            </div>
          )}

          {/* Key Metrics */}
          {loading ? (
            <div className="loading">Loading metrics...</div>
          ) : (
            <>
              <div className="metrics-grid">
                {performance && (
                  <>
                    <MetricCard
                      icon={Zap}
                      label="Total Executions"
                      value={performance.total_executions}
                    />
                    <MetricCard
                      icon={CheckCircle}
                      label="Success Rate"
                      value={performance.success_rate}
                      unit="%"
                    />
                    <MetricCard
                      icon={Clock}
                      label="Avg Execution Time"
                      value={performance.average_execution_time_seconds}
                      unit="s"
                    />
                    <MetricCard
                      icon={DollarSign}
                      label="Estimated Cost"
                      value={costs?.total_cost || 0}
                      unit="$"
                    />
                  </>
                )}
              </div>

              {/* Charts and Analytics */}
              <div className="analytics-grid">
                <div className="analytics-card">
                  <PerformanceChart />
                </div>
                <div className="analytics-card">
                  <CostBreakdown />
                </div>
                <div className="analytics-card full-width">
                  <ErrorAnalytics />
                </div>
              </div>

              {/* Percentiles */}
              {performance && (
                <div className="percentiles-section">
                  <h3>Execution Time Percentiles</h3>
                  <div className="percentiles-grid">
                    <div className="percentile-item">
                      <label>P50</label>
                      <p>{performance.p50?.toFixed(3) || 'N/A'}s</p>
                    </div>
                    <div className="percentile-item">
                      <label>P95</label>
                      <p>{performance.p95?.toFixed(3) || 'N/A'}s</p>
                    </div>
                    <div className="percentile-item">
                      <label>P99</label>
                      <p>{performance.p99?.toFixed(3) || 'N/A'}s</p>
                    </div>
                    <div className="percentile-item">
                      <label>Max</label>
                      <p>{performance.max?.toFixed(3) || 'N/A'}s</p>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
};

export default AgentMonitor;
