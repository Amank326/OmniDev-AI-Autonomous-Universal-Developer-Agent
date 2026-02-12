/**
 * MetricsVisualization Component
 * Advanced metrics visualization with charts, trends, and analysis
 */

import React, { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, BarChart, Bar, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';

const MetricsVisualization = ({ workspaceId, onError }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [metrics, setMetrics] = useState([]);
  const [selectedMetrics, setSelectedMetrics] = useState([]);
  const [timeRange, setTimeRange] = useState('7d');
  const [chartType, setChartType] = useState('line');
  const [loading, setLoading] = useState(false);
  const [aggregationLevel, setAggregationLevel] = useState('hour');
  const [searchTerm, setSearchTerm] = useState('');
  const [trends, setTrends] = useState({});
  const [anomalies, setAnomalies] = useState([]);
  const [showAnomalies, setShowAnomalies] = useState(true);

  // Fetch metrics data
  const fetchMetrics = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/v1/analytics/metrics/series/all?workspace_id=${workspaceId}&granularity=${aggregationLevel}&limit=500`
      );
      
      if (!response.ok) throw new Error('Failed to fetch metrics');
      
      const data = await response.json();
      setMetrics(data.data || []);
    } catch (error) {
      onError?.(error);
    } finally {
      setLoading(false);
    }
  }, [workspaceId, aggregationLevel, onError]);

  // Fetch trends
  const fetchTrends = useCallback(async () => {
    try {
      const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 1;
      const response = await fetch(
        `/api/v1/analytics/trends/trending-metrics?workspace_id=${workspaceId}&days=${days}`
      );
      
      if (!response.ok) throw new Error('Failed to fetch trends');
      
      const data = await response.json();
      setTrends(data.trending_metrics || {});
    } catch (error) {
      onError?.(error);
    }
  }, [workspaceId, timeRange, onError]);

  // Detect anomalies
  const detectAnomalies = useCallback(async () => {
    try {
      const response = await fetch(
        `/api/v1/analytics/anomalies/all?workspace_id=${workspaceId}&sensitivity=1.0`
      );
      
      if (!response.ok) throw new Error('Failed to detect anomalies');
      
      const data = await response.json();
      setAnomalies(data.anomalies || []);
    } catch (error) {
      onError?.(error);
    }
  }, [workspaceId, onError]);

  useEffect(() => {
    fetchMetrics();
    fetchTrends();
    detectAnomalies();
  }, [fetchMetrics, fetchTrends, detectAnomalies]);

  // Filter metrics based on search
  const filteredMetrics = selectedMetrics.length === 0 
    ? metrics 
    : metrics.filter(m => selectedMetrics.includes(m.metric_type));

  // Search metrics
  const searchedMetrics = searchTerm
    ? filteredMetrics.filter(m => m.metric_type.toLowerCase().includes(searchTerm.toLowerCase()))
    : filteredMetrics;

  // Get unique metric types
  const metricTypes = [...new Set(metrics.map(m => m.metric_type))];

  // Prepare chart data
  const chartData = searchedMetrics.slice(0, 100).map(m => ({
    timestamp: new Date(m.timestamp).toLocaleTimeString(),
    ...m.dimensions,
    value: m.value,
    metric_type: m.metric_type,
  }));

  // Highlight anomalies
  const anomalyPoints = anomalies.filter(a => selectedMetrics.length === 0 || selectedMetrics.includes(a.metric_type));

  return (
    <div className="metrics-visualization">
      <style>{`
        .metrics-visualization {
          padding: 20px;
          background: #f5f5f5;
          border-radius: 8px;
        }
        
        .mv-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          flex-wrap: wrap;
          gap: 10px;
        }
        
        .mv-title {
          font-size: 24px;
          font-weight: bold;
          color: #333;
        }
        
        .mv-controls {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
        }
        
        .control-group {
          display: flex;
          align-items: center;
          gap: 8px;
          background: white;
          padding: 8px 12px;
          border-radius: 4px;
          border: 1px solid #ddd;
        }
        
        .control-group label {
          font-weight: 600;
          font-size: 12px;
          color: #666;
        }
        
        .control-group select,
        .control-group input {
          padding: 6px 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 13px;
        }
        
        .tabs {
          display: flex;
          gap: 0;
          margin-bottom: 20px;
          border-bottom: 2px solid #ddd;
        }
        
        .tab {
          padding: 12px 20px;
          cursor: pointer;
          border: none;
          background: none;
          font-size: 14px;
          font-weight: 600;
          color: #666;
          border-bottom: 3px solid transparent;
          transition: all 0.2s;
        }
        
        .tab.active {
          color: #2563eb;
          border-bottom-color: #2563eb;
        }
        
        .tab:hover {
          color: #2563eb;
        }
        
        .chart-container {
          background: white;
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 20px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .chart-title {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 15px;
          color: #333;
        }
        
        .metrics-filter {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-bottom: 15px;
        }
        
        .metric-chip {
          padding: 6px 12px;
          border-radius: 20px;
          cursor: pointer;
          border: 2px solid #ddd;
          background: white;
          font-size: 13px;
          transition: all 0.2s;
        }
        
        .metric-chip.selected {
          background: #2563eb;
          color: white;
          border-color: #2563eb;
        }
        
        .metric-chip:hover {
          border-color: #2563eb;
        }
        
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          margin-bottom: 20px;
        }
        
        .stat-card {
          background: white;
          padding: 15px;
          border-radius: 8px;
          border-left: 4px solid #2563eb;
        }
        
        .stat-label {
          font-size: 12px;
          color: #666;
          font-weight: 600;
          margin-bottom: 5px;
        }
        
        .stat-value {
          font-size: 24px;
          font-weight: bold;
          color: #333;
        }
        
        .stat-change {
          font-size: 12px;
          margin-top: 5px;
          color: #10b981;
        }
        
        .stat-change.negative {
          color: #ef4444;
        }
        
        .anomalies-list {
          background: white;
          border-radius: 8px;
          padding: 15px;
          margin-top: 15px;
        }
        
        .anomaly-item {
          padding: 10px;
          background: #fef3c7;
          border-left: 4px solid #f59e0b;
          border-radius: 4px;
          margin-bottom: 10px;
          font-size: 13px;
        }
        
        .anomaly-item strong {
          display: block;
          color: #92400e;
          margin-bottom: 3px;
        }
        
        .no-data {
          text-align: center;
          padding: 40px 20px;
          color: #999;
        }
        
        .loading {
          text-align: center;
          padding: 40px 20px;
          color: #999;
        }
        
        .search-box {
          flex: 1;
          min-width: 250px;
        }
        
        .search-box input {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 13px;
        }
      `}</style>

      <div className="mv-header">
        <div className="mv-title">📊 Metrics Visualization</div>
        <div className="mv-controls">
          <div className="control-group search-box">
            <input
              type="text"
              placeholder="Search metrics..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="control-group">
            <label>Time Range:</label>
            <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
              <option value="1d">Last 24h</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
            </select>
          </div>
          <div className="control-group">
            <label>Chart Type:</label>
            <select value={chartType} onChange={(e) => setChartType(e.target.value)}>
              <option value="line">Line Chart</option>
              <option value="bar">Bar Chart</option>
              <option value="area">Area Chart</option>
              <option value="scatter">Scatter Plot</option>
            </select>
          </div>
          <div className="control-group">
            <label>Granularity:</label>
            <select value={aggregationLevel} onChange={(e) => setAggregationLevel(e.target.value)}>
              <option value="minute">1 Minute</option>
              <option value="hour">Hourly</option>
              <option value="day">Daily</option>
            </select>
          </div>
        </div>
      </div>

      <div className="tabs">
        <button className={`tab ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>
          📈 Overview
        </button>
        <button className={`tab ${activeTab === 'trends' ? 'active' : ''}`} onClick={() => setActiveTab('trends')}>
          📊 Trends
        </button>
        <button className={`tab ${activeTab === 'anomalies' ? 'active' : ''}`} onClick={() => setActiveTab('anomalies')}>
          ⚠️ Anomalies
        </button>
        <button className={`tab ${activeTab === 'details' ? 'active' : ''}`} onClick={() => setActiveTab('details')}>
          🔍 Details
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading metrics data...</div>
      ) : (
        <>
          {activeTab === 'overview' && (
            <div>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-label">Total Metrics</div>
                  <div className="stat-value">{metricTypes.length}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Data Points</div>
                  <div className="stat-value">{chartData.length}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Anomalies Detected</div>
                  <div className="stat-value">{anomalies.length}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Avg Value</div>
                  <div className="stat-value">
                    {chartData.length > 0 
                      ? (chartData.reduce((sum, d) => sum + d.value, 0) / chartData.length).toFixed(2)
                      : '0'}
                  </div>
                </div>
              </div>

              <div className="chart-container">
                <div className="chart-title">Metric Trends</div>
                <div className="metrics-filter">
                  {metricTypes.map(type => (
                    <button
                      key={type}
                      className={`metric-chip ${selectedMetrics.includes(type) ? 'selected' : ''}`}
                      onClick={() => {
                        setSelectedMetrics(prev =>
                          prev.includes(type)
                            ? prev.filter(m => m !== type)
                            : [...prev, type]
                        );
                      }}
                    >
                      {type}
                    </button>
                  ))}
                </div>

                {chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={400}>
                    {chartType === 'line' && (
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="timestamp" fontSize={12} />
                        <YAxis fontSize={12} />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="value" stroke="#2563eb" dot={false} />
                      </LineChart>
                    )}
                    {chartType === 'bar' && (
                      <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="timestamp" fontSize={12} />
                        <YAxis fontSize={12} />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="value" fill="#2563eb" />
                      </BarChart>
                    )}
                    {chartType === 'area' && (
                      <AreaChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="timestamp" fontSize={12} />
                        <YAxis fontSize={12} />
                        <Tooltip />
                        <Legend />
                        <Area type="monotone" dataKey="value" fill="#2563eb" stroke="#2563eb" />
                      </AreaChart>
                    )}
                    {chartType === 'scatter' && (
                      <ScatterChart>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="timestamp" fontSize={12} />
                        <YAxis fontSize={12} />
                        <Tooltip />
                        <Scatter name="Metrics" data={chartData} fill="#2563eb" />
                      </ScatterChart>
                    )}
                  </ResponsiveContainer>
                ) : (
                  <div className="no-data">No data available</div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'trends' && (
            <div className="chart-container">
              <div className="chart-title">Trending Metrics</div>
              {Object.keys(trends).length > 0 ? (
                <div className="stats-grid">
                  {Object.entries(trends).map(([metricType, trendData]) => (
                    <div key={metricType} className="stat-card">
                      <div className="stat-label">{metricType}</div>
                      <div className="stat-value">{trendData.trend || 'stable'}</div>
                      <div className={`stat-change ${trendData.strength < 0 ? 'negative' : ''}`}>
                        Strength: {(trendData.strength || 0).toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-data">No trend data available</div>
              )}
            </div>
          )}

          {activeTab === 'anomalies' && (
            <div className="chart-container">
              <div className="chart-title">Detected Anomalies</div>
              {anomalies.length > 0 ? (
                <div className="anomalies-list">
                  {anomalies.map((anomaly, idx) => (
                    <div key={idx} className="anomaly-item">
                      <strong>{anomaly.metric_type}</strong>
                      Value: {anomaly.value?.toFixed(2) || 'N/A'} at {new Date(anomaly.timestamp).toLocaleString()}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-data">No anomalies detected</div>
              )}
            </div>
          )}

          {activeTab === 'details' && (
            <div className="chart-container">
              <div className="chart-title">Detailed Metrics</div>
              {chartData.length > 0 ? (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{
                    width: '100%',
                    fontSize: '13px',
                    borderCollapse: 'collapse',
                  }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid #ddd' }}>
                        <th style={{ padding: '10px', textAlign: 'left' }}>Timestamp</th>
                        <th style={{ padding: '10px', textAlign: 'left' }}>Metric Type</th>
                        <th style={{ padding: '10px', textAlign: 'right' }}>Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {chartData.slice(0, 50).map((row, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                          <td style={{ padding: '8px' }}>{row.timestamp}</td>
                          <td style={{ padding: '8px' }}>{row.metric_type}</td>
                          <td style={{ padding: '8px', textAlign: 'right' }}>{row.value?.toFixed(2) || 'N/A'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="no-data">No detailed data available</div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default MetricsVisualization;
