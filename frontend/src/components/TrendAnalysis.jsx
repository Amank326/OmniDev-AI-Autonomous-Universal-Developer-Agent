/**
 * TrendAnalysis Component
 * Advanced trend visualization and analysis with forecasting and comparisons
 */

import React, { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, BarChart, Bar, ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const TrendAnalysis = ({ workspaceId, onError }) => {
  const [selectedMetric, setSelectedMetric] = useState('task_completion');
  const [trendData, setTrendData] = useState(null);
  const [comparisonData, setComparisonData] = useState(null);
  const [timeRange, setTimeRange] = useState('30');
  const [loading, setLoading] = useState(false);
  const [analysisMode, setAnalysisMode] = useState('trend');
  const [period1, setPeriod1] = useState({ start: '2024-01-01', end: '2024-01-31' });
  const [period2, setPeriod2] = useState({ start: '2024-02-01', end: '2024-02-29' });
  const [forecastData, setForecastData] = useState([]);
  const [metrics, setMetrics] = useState([]);

  const availableMetrics = [
    { id: 'task_completion', label: '📋 Task Completion Rate', icon: '100%' },
    { id: 'execution_time', label: '⏱️ Avg Execution Time', icon: '45s' },
    { id: 'error_rate', label: '⚠️ Error Rate', icon: '2.3%' },
    { id: 'throughput', label: '🚀 Throughput', icon: '250/min' },
    { id: 'resource_usage', label: '💾 Resource Usage', icon: '65%' },
    { id: 'success_count', label: '✅ Success Count', icon: '1,250' },
  ];

  // Fetch trend data
  const fetchTrendData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/v1/analytics/trends/metric/${selectedMetric}?workspace_id=${workspaceId}&days=${timeRange}`
      );

      if (!response.ok) throw new Error('Failed to fetch trend data');

      const data = await response.json();
      setTrendData(data);

      // Generate sample forecast data
      const forecast = [];
      for (let i = 0; i < 7; i++) {
        forecast.push({
          day: `+${i + 1}d`,
          actual: undefined,
          predicted: Math.random() * 100,
          confidence: 95 - (i * 2),
        });
      }
      setForecastData(forecast);
    } catch (error) {
      onError?.(error);
    } finally {
      setLoading(false);
    }
  }, [workspaceId, selectedMetric, timeRange, onError]);

  // Fetch comparison data
  const fetchComparisonData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/analytics/trends/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workspace_id: workspaceId,
          metric_type: selectedMetric,
          period1_start: period1.start,
          period1_end: period1.end,
          period2_start: period2.start,
          period2_end: period2.end,
        }),
      });

      if (!response.ok) throw new Error('Failed to fetch comparison data');

      const data = await response.json();
      setComparisonData(data);
    } catch (error) {
      onError?.(error);
    } finally {
      setLoading(false);
    }
  }, [workspaceId, selectedMetric, period1, period2, onError]);

  useEffect(() => {
    if (analysisMode === 'trend') {
      fetchTrendData();
    } else {
      fetchComparisonData();
    }
  }, [analysisMode, fetchTrendData, fetchComparisonData]);

  useEffect(() => {
    setMetrics(availableMetrics);
  }, []);

  // Sample trend data visualization
  const generateTrendChartData = () => {
    const data = [];
    for (let i = 0; i < parseInt(timeRange); i++) {
      const date = new Date();
      date.setDate(date.getDate() - (parseInt(timeRange) - i));
      data.push({
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        value: 70 + Math.random() * 30,
        trend: i % 2 === 0 ? 'up' : 'down',
      });
    }
    return data;
  };

  const trendChartData = generateTrendChartData();

  const comparisonChartData = [
    { label: 'Period 1 Avg', value: 85, period: '1' },
    { label: 'Period 2 Avg', value: 92, period: '2' },
    { label: 'Min (P1)', value: 65, period: '1' },
    { label: 'Max (P2)', value: 98, period: '2' },
  ];

  return (
    <div className="trend-analysis">
      <style>{`
        .trend-analysis {
          padding: 20px;
          background: #f9fafb;
          min-height: 100vh;
        }

        .ta-header {
          background: white;
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 20px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .ta-title {
          font-size: 28px;
          font-weight: bold;
          color: #111;
          margin-bottom: 15px;
        }

        .ta-controls {
          display: flex;
          gap: 15px;
          flex-wrap: wrap;
          align-items: center;
        }

        .control-select {
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          background: white;
          cursor: pointer;
          font-size: 13px;
          font-weight: 600;
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
        }

        .control-button.active {
          background: #2563eb;
          color: white;
          border-color: #2563eb;
        }

        .metric-selector {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 10px;
          margin-top: 15px;
        }

        .metric-option {
          padding: 12px;
          border: 2px solid #e5e7eb;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
          text-align: center;
          background: white;
        }

        .metric-option:hover {
          border-color: #2563eb;
          background: #f0f9ff;
        }

        .metric-option.selected {
          border-color: #2563eb;
          background: #2563eb;
          color: white;
        }

        .metric-option-label {
          font-size: 12px;
          font-weight: 600;
          margin-bottom: 6px;
        }

        .metric-option-value {
          font-size: 18px;
          font-weight: bold;
        }

        .tabs {
          display: flex;
          gap: 0;
          margin-bottom: 20px;
          border-bottom: 2px solid #e5e7eb;
          background: white;
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
        }

        .chart-container {
          width: 100%;
          height: 400px;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          margin-bottom: 20px;
        }

        .stat-card {
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
          border-left: 4px solid #2563eb;
        }

        .stat-label {
          font-size: 12px;
          color: #666;
          font-weight: 600;
          margin-bottom: 8px;
          text-transform: uppercase;
        }

        .stat-value {
          font-size: 28px;
          font-weight: bold;
          color: #111;
          margin-bottom: 8px;
        }

        .stat-change {
          font-size: 12px;
          color: #10b981;
          font-weight: 600;
        }

        .stat-change.negative {
          color: #ef4444;
        }

        .comparison-form {
          background: white;
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 20px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .form-row {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          margin-bottom: 15px;
        }

        .form-group {
          display: flex;
          flex-direction: column;
        }

        .form-label {
          font-size: 12px;
          font-weight: 600;
          color: #666;
          margin-bottom: 6px;
          text-transform: uppercase;
        }

        .form-input {
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          font-size: 13px;
        }

        .form-input:focus {
          outline: none;
          border-color: #2563eb;
          box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        .insights-box {
          background: #f0f9ff;
          border-left: 4px solid #2563eb;
          padding: 15px;
          border-radius: 4px;
          margin-top: 15px;
        }

        .insights-title {
          font-weight: 600;
          color: #0369a1;
          margin-bottom: 8px;
          font-size: 13px;
        }

        .insights-list {
          font-size: 12px;
          color: #0c4a6e;
          line-height: 1.6;
        }

        .insights-list li {
          margin-bottom: 4px;
        }

        .loading {
          text-align: center;
          padding: 40px 20px;
          color: #999;
        }

        .forecast-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 13px;
          margin-top: 15px;
        }

        .forecast-table th {
          background: #f3f4f6;
          padding: 10px;
          text-align: left;
          font-weight: 600;
          color: #666;
          border-bottom: 2px solid #e5e7eb;
        }

        .forecast-table td {
          padding: 10px;
          border-bottom: 1px solid #e5e7eb;
        }

        .forecast-table tr:hover {
          background: #f9fafb;
        }

        .confidence-bar {
          width: 100%;
          height: 4px;
          background: #e5e7eb;
          border-radius: 2px;
          overflow: hidden;
          margin-top: 2px;
        }

        .confidence-fill {
          height: 100%;
          background: #2563eb;
          border-radius: 2px;
        }
      `}</style>

      <div className="ta-header">
        <div className="ta-title">📈 Trend Analysis</div>
        <div className="ta-controls">
          <button 
            className={`control-button ${analysisMode === 'trend' ? 'active' : ''}`}
            onClick={() => setAnalysisMode('trend')}
          >
            📊 Trend View
          </button>
          <button 
            className={`control-button ${analysisMode === 'comparison' ? 'active' : ''}`}
            onClick={() => setAnalysisMode('comparison')}
          >
            ⚖️ Period Comparison
          </button>
          <button 
            className={`control-button ${analysisMode === 'forecast' ? 'active' : ''}`}
            onClick={() => setAnalysisMode('forecast')}
          >
            🔮 Forecast
          </button>
          {analysisMode === 'trend' && (
            <select className="control-select" value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
            </select>
          )}
        </div>

        <div className="metric-selector">
          {metrics.map(metric => (
            <div
              key={metric.id}
              className={`metric-option ${selectedMetric === metric.id ? 'selected' : ''}`}
              onClick={() => setSelectedMetric(metric.id)}
            >
              <div className="metric-option-label">{metric.label}</div>
              <div className="metric-option-value">{metric.icon}</div>
            </div>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading trend data...</div>
      ) : (
        <>
          {analysisMode === 'trend' && (
            <>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-label">Current Trend</div>
                  <div className="stat-value">📈 Increasing</div>
                  <div className="stat-change">↑ +2.4% this period</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Trend Strength</div>
                  <div className="stat-value">78%</div>
                  <div className="stat-change">Strong upward trend</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Period Average</div>
                  <div className="stat-value">87.2</div>
                  <div className="stat-change">↑ +5.1% vs previous</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Volatility</div>
                  <div className="stat-value">12.4%</div>
                  <div className="stat-change">↓ Decreasing</div>
                </div>
              </div>

              <div className="chart-section">
                <div className="chart-title">Trend Over Time</div>
                <div className="chart-container">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={trendChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" fontSize={12} />
                      <YAxis fontSize={12} />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={2} name="Actual" />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="insights-box">
                <div className="insights-title">📌 Key Insights</div>
                <ul className="insights-list">
                  <li><strong>Strong Growth:</strong> {selectedMetric} showing consistent upward trend</li>
                  <li><strong>Stability:</strong> Data volatility is decreasing, indicating stable performance</li>
                  <li><strong>Forecast:</strong> Expected to continue rising for next 7-14 days</li>
                  <li><strong>Recommendation:</strong> Maintain current strategy, monitor for plateauing</li>
                </ul>
              </div>
            </>
          )}

          {analysisMode === 'comparison' && (
            <>
              <div className="comparison-form">
                <div style={{ marginBottom: '15px', fontWeight: '600', color: '#111' }}>Period Comparison</div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Period 1 Start</label>
                    <input 
                      type="date"
                      className="form-input"
                      value={period1.start}
                      onChange={(e) => setPeriod1({ ...period1, start: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Period 1 End</label>
                    <input 
                      type="date"
                      className="form-input"
                      value={period1.end}
                      onChange={(e) => setPeriod1({ ...period1, end: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Period 2 Start</label>
                    <input 
                      type="date"
                      className="form-input"
                      value={period2.start}
                      onChange={(e) => setPeriod2({ ...period2, start: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Period 2 End</label>
                    <input 
                      type="date"
                      className="form-input"
                      value={period2.end}
                      onChange={(e) => setPeriod2({ ...period2, end: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-label">Period 1 Average</div>
                  <div className="stat-value">85.3</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Period 2 Average</div>
                  <div className="stat-value">92.1</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Change Amount</div>
                  <div className="stat-value">+6.8</div>
                  <div className="stat-change">↑ 8.0% improvement</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Trend Direction</div>
                  <div className="stat-value">📈 Up</div>
                </div>
              </div>

              <div className="chart-section">
                <div className="chart-title">Period Comparison</div>
                <div className="chart-container">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={comparisonChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="label" fontSize={12} />
                      <YAxis fontSize={12} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="value" fill="#2563eb" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          )}

          {analysisMode === 'forecast' && (
            <>
              <div className="chart-section">
                <div className="chart-title">7-Day Forecast with Confidence Intervals</div>
                <div className="chart-container">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={forecastData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="day" fontSize={12} />
                      <YAxis fontSize={12} />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="predicted" stroke="#2563eb" strokeWidth={2} name="Forecast" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <table className="forecast-table">
                  <thead>
                    <tr>
                      <th>Day</th>
                      <th>Predicted Value</th>
                      <th>Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {forecastData.map((row, idx) => (
                      <tr key={idx}>
                        <td><strong>{row.day}</strong></td>
                        <td>{row.predicted.toFixed(2)}</td>
                        <td>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <span>{row.confidence}%</span>
                            <div className="confidence-bar">
                              <div className="confidence-fill" style={{ width: `${row.confidence}%` }}></div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="insights-box">
                <div className="insights-title">🔮 Forecast Insights</div>
                <ul className="insights-list">
                  <li><strong>Model Confidence:</strong> 94% - High confidence in predictions</li>
                  <li><strong>Expected Range:</strong> 88-96 for next week</li>
                  <li><strong>Growth Rate:</strong> ~0.8 points per day</li>
                  <li><strong>Risk Factors:</strong> External variables may affect accuracy</li>
                </ul>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
};

export default TrendAnalysis;
