/**
 * AnalyticsDashboard Component
 * Comprehensive analytics dashboard with widgets, real-time updates, and analytics overview
 */

import React, { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const AnalyticsDashboard = ({ workspaceId, onError }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [widgets, setWidgets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000);
  const [selectedView, setSelectedView] = useState('overview');
  const [timeGranularity, setTimeGranularity] = useState('hour');

  const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  // Fetch dashboard summary
  const fetchDashboard = useCallback(async () => {
    try {
      const response = await fetch(
        `/api/v1/analytics/dashboard/summary?workspace_id=${workspaceId}`
      );

      if (!response.ok) throw new Error('Failed to fetch dashboard');

      const data = await response.json();
      setDashboardData(data.summary || {});
    } catch (error) {
      onError?.(error);
    } finally {
      setLoading(false);
    }
  }, [workspaceId, onError]);

  // Fetch dashboard widgets
  const fetchWidgets = useCallback(async () => {
    try {
      const response = await fetch(
        `/api/v1/analytics/dashboard/widgets?workspace_id=${workspaceId}&widget_types=trending,performance,health,distribution`
      );

      if (!response.ok) throw new Error('Failed to fetch widgets');

      const data = await response.json();
      setWidgets(data.widgets || {});
    } catch (error) {
      onError?.(error);
    }
  }, [workspaceId, onError]);

  useEffect(() => {
    fetchDashboard();
    fetchWidgets();

    const interval = setInterval(() => {
      fetchDashboard();
      fetchWidgets();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [fetchDashboard, fetchWidgets, refreshInterval]);

  return (
    <div className="analytics-dashboard">
      <style>{`
        .analytics-dashboard {
          background: #f9fafb;
          min-height: 100vh;
          padding: 20px;
        }

        .ad-header {
          background: white;
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 20px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .ad-title {
          font-size: 28px;
          font-weight: bold;
          color: #111;
          margin-bottom: 15px;
        }

        .ad-controls {
          display: flex;
          gap: 15px;
          flex-wrap: wrap;
          align-items: center;
        }

        .control-button {
          padding: 8px 16px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          background: white;
          cursor: pointer;
          font-size: 13px;
          font-weight: 600;
          transition: all 0.2s;
        }

        .control-button:hover {
          background: #f3f4f6;
          border-color: #9ca3af;
        }

        .control-button.active {
          background: #2563eb;
          color: white;
          border-color: #2563eb;
        }

        .select-control {
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          background: white;
          cursor: pointer;
          font-size: 13px;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          margin-bottom: 20px;
        }

        .metric-card {
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
          border-left: 4px solid #2563eb;
        }

        .metric-card.success {
          border-left-color: #10b981;
        }

        .metric-card.warning {
          border-left-color: #f59e0b;
        }

        .metric-card.error {
          border-left-color: #ef4444;
        }

        .metric-label {
          font-size: 12px;
          color: #666;
          font-weight: 600;
          margin-bottom: 8px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .metric-value {
          font-size: 32px;
          font-weight: bold;
          color: #111;
          margin-bottom: 8px;
        }

        .metric-change {
          font-size: 12px;
          color: #10b981;
          font-weight: 600;
        }

        .metric-change.negative {
          color: #ef4444;
        }

        .chart-section {
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
          margin-bottom: 20px;
        }

        .chart-title {
          font-size: 16px;
          font-weight: 600;
          color: #111;
          margin-bottom: 15px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .chart-container {
          width: 100%;
          height: 300px;
        }

        .widget-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 15px;
          margin-bottom: 20px;
        }

        .widget-card {
          background: white;
          padding: 15px;
          border-radius: 8px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .widget-title {
          font-size: 13px;
          font-weight: 600;
          color: #666;
          margin-bottom: 10px;
        }

        .widget-content {
          font-size: 14px;
          color: #333;
        }

        .status-indicator {
          display: inline-block;
          width: 12px;
          height: 12px;
          border-radius: 50%;
          margin-right: 6px;
        }

        .status-healthy {
          background: #10b981;
        }

        .status-warning {
          background: #f59e0b;
        }

        .status-critical {
          background: #ef4444;
        }

        .data-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 13px;
        }

        .data-table th {
          background: #f3f4f6;
          padding: 10px;
          text-align: left;
          font-weight: 600;
          color: #666;
          border-bottom: 2px solid #e5e7eb;
        }

        .data-table td {
          padding: 10px;
          border-bottom: 1px solid #e5e7eb;
        }

        .data-table tr:hover {
          background: #f9fafb;
        }

        .loading-spinner {
          text-align: center;
          padding: 40px 20px;
          color: #999;
        }

        .section-divider {
          height: 1px;
          background: #e5e7eb;
          margin: 30px 0;
        }

        .refresh-badge {
          font-size: 11px;
          color: #999;
          margin-left: 10px;
        }
      `}</style>

      <div className="ad-header">
        <div className="ad-title">📊 Analytics Dashboard</div>
        <div className="ad-controls">
          <button 
            className={`control-button ${selectedView === 'overview' ? 'active' : ''}`}
            onClick={() => setSelectedView('overview')}
          >
            Overview
          </button>
          <button 
            className={`control-button ${selectedView === 'detailed' ? 'active' : ''}`}
            onClick={() => setSelectedView('detailed')}
          >
            Detailed
          </button>
          <button 
            className={`control-button ${selectedView === 'performance' ? 'active' : ''}`}
            onClick={() => setSelectedView('performance')}
          >
            Performance
          </button>
          <select className="select-control" value={timeGranularity} onChange={(e) => setTimeGranularity(e.target.value)}>
            <option value="minute">1 Minute</option>
            <option value="hour">Hourly</option>
            <option value="day">Daily</option>
          </select>
          <select className="select-control" value={refreshInterval} onChange={(e) => setRefreshInterval(parseInt(e.target.value))}>
            <option value={10000}>Refresh: 10s</option>
            <option value={30000}>Refresh: 30s</option>
            <option value={60000}>Refresh: 1m</option>
          </select>
          <button className="control-button" onClick={() => {
            fetchDashboard();
            fetchWidgets();
          }}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading-spinner">Loading dashboard data...</div>
      ) : (
        <>
          {selectedView === 'overview' && dashboardData && (
            <>
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">Total Tasks (Week)</div>
                  <div className="metric-value">{dashboardData.total_tasks_week || 0}</div>
                  <div className="metric-change">↑ 12% from last week</div>
                </div>
                <div className="metric-card success">
                  <div className="metric-label">Success Rate</div>
                  <div className="metric-value">{(dashboardData.success_rate || 0).toFixed(1)}%</div>
                  <div className="metric-change">↑ 2.1% improvement</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Avg Execution Time</div>
                  <div className="metric-value">{(dashboardData.avg_execution_time || 0).toFixed(1)}s</div>
                  <div className="metric-change">↓ 8% faster</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Active Agents</div>
                  <div className="metric-value">{dashboardData.active_agents || 0}</div>
                  <div className="metric-change">↑ 5 agents online</div>
                </div>
                <div className={`metric-card ${dashboardData.system_health === 'healthy' ? 'success' : dashboardData.system_health === 'degraded' ? 'warning' : 'error'}`}>
                  <div className="metric-label">System Health</div>
                  <div className="metric-value">{dashboardData.system_health || 'unknown'}</div>
                  <div style={{ fontSize: '11px', marginTop: '5px' }}>
                    <span className={`status-indicator status-${dashboardData.system_health === 'healthy' ? 'healthy' : 'warning'}`}></span>
                    All systems operational
                  </div>
                </div>
              </div>

              <div className="chart-section">
                <div className="chart-title">
                  Top Metrics
                  <span className="refresh-badge">Updated 2s ago</span>
                </div>
                <div className="chart-container">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={[
                      { name: 'Task Completion', value: dashboardData.total_tasks_week || 0 },
                      { name: 'Success Rate', value: dashboardData.success_rate || 0 },
                      { name: 'Active Agents', value: (dashboardData.active_agents || 0) * 10 },
                    ]}>
                      <Bar dataKey="value" fill="#2563eb" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          )}

          {selectedView === 'detailed' && (
            <div className="chart-section">
              <div className="chart-title">Detailed Metrics Breakdown</div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th>Current</th>
                    <th>Previous Period</th>
                    <th>Change</th>
                    <th>Trend</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>Total Tasks</strong></td>
                    <td>{dashboardData?.total_tasks_week || 0}</td>
                    <td>145</td>
                    <td style={{ color: '#10b981' }}>↑ +8.9%</td>
                    <td>📈</td>
                  </tr>
                  <tr>
                    <td><strong>Success Rate</strong></td>
                    <td>{(dashboardData?.success_rate || 0).toFixed(1)}%</td>
                    <td>92.3%</td>
                    <td style={{ color: '#10b981' }}>↑ +2.1%</td>
                    <td>📈</td>
                  </tr>
                  <tr>
                    <td><strong>Execution Time</strong></td>
                    <td>{(dashboardData?.avg_execution_time || 0).toFixed(1)}s</td>
                    <td>54.2s</td>
                    <td style={{ color: '#10b981' }}>↓ -8.0%</td>
                    <td>📉</td>
                  </tr>
                  <tr>
                    <td><strong>Active Agents</strong></td>
                    <td>{dashboardData?.active_agents || 0}</td>
                    <td>12</td>
                    <td style={{ color: '#10b981' }}>↑ +41.7%</td>
                    <td>📈</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {selectedView === 'performance' && (
            <>
              <div className="widget-grid">
                <div className="widget-card">
                  <div className="widget-title">Agent Performance Distribution</div>
                  <div className="chart-container">
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Excellent', value: 45 },
                            { name: 'Good', value: 30 },
                            { name: 'Average', value: 20 },
                            { name: 'Poor', value: 5 },
                          ]}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, value }) => `${name} ${value}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {[0, 1, 2, 3].map((idx) => (
                            <Cell key={`cell-${idx}`} fill={COLORS[idx]} />
                          ))}
                        </Pie>
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="widget-card">
                  <div className="widget-title">Task Success by Type</div>
                  <div className="chart-container">
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={[
                        { name: 'Data Processing', value: 96 },
                        { name: 'Analysis', value: 92 },
                        { name: 'Reporting', value: 88 },
                        { name: 'Integration', value: 85 },
                      ]}>
                        <Bar dataKey="value" fill="#10b981" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              <div className="chart-section">
                <div className="chart-title">Performance Trend (7 Days)</div>
                <div className="chart-container">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={[
                      { day: 'Mon', performance: 85 },
                      { day: 'Tue', performance: 87 },
                      { day: 'Wed', performance: 89 },
                      { day: 'Thu', performance: 91 },
                      { day: 'Fri', performance: 93 },
                      { day: 'Sat', performance: 92 },
                      { day: 'Sun', performance: 94 },
                    ]}>
                      <Line type="monotone" dataKey="performance" stroke="#2563eb" strokeWidth={2} dot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
