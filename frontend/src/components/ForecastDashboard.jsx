import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ComposedChart
} from 'recharts';
import './ForecastDashboard.css';

const ForecastDashboard = ({ workspaceId, onAlertTriggered }) => {
  const [forecasts, setForecasts] = useState({});
  const [selectedMetric, setSelectedMetric] = useState('execution_time');
  const [selectedModel, setSelectedModel] = useState('exponential_smoothing');
  const [predictions, setPredictions] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loadingForecasts, setLoadingForecasts] = useState(false);
  const [loadingPredictions, setLoadingPredictions] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(300000); // 5 minutes
  const [viewMode, setViewMode] = useState('overview'); // overview, detailed, models
  const [confidenceLevel, setConfidenceLevel] = useState(0.95);
  const [periods, setPeriods] = useState(7);
  const [riskScore, setRiskScore] = useState(0);
  const [performanceScore, setPerformanceScore] = useState(0);

  // Available metrics
  const metrics = [
    { id: 'execution_time', label: 'Execution Time (ms)', color: '#8884d8' },
    { id: 'error_rate', label: 'Error Rate (%)', color: '#82ca9d' },
    { id: 'throughput', label: 'Throughput (ops/s)', color: '#ffc658' },
    { id: 'resource_usage', label: 'Resource Usage (%)', color: '#ff7c7c' },
    { id: 'agent_load', label: 'Agent Load', color: '#8dd1e1' },
  ];

  // Available models
  const models = [
    { id: 'exponential_smoothing', label: 'Exponential Smoothing' },
    { id: 'linear_regression', label: 'Linear Regression' },
    { id: 'moving_average', label: 'Moving Average' },
    { id: 'polynomial', label: 'Polynomial' },
    { id: 'ensemble', label: 'Ensemble' },
  ];

  // Fetch forecast data
  const fetchForecast = useCallback(async () => {
    setLoadingForecasts(true);
    try {
      // Mock API call
      const response = await new Promise(resolve => {
        setTimeout(() => {
          resolve({
            metric_name: selectedMetric,
            model: selectedModel,
            forecast_points: generateMockForecastPoints(),
            rmse: 12.5,
            mape: 0.08,
            r_squared: 0.92,
            confidence: confidenceLevel,
            seasonality: 'weekly',
            trend: 'increasing',
          });
        }, 500);
      });

      setForecasts(prev => ({
        ...prev,
        [selectedMetric]: response,
      }));
    } catch (error) {
      console.error('Forecast fetch error:', error);
    } finally {
      setLoadingForecasts(false);
    }
  }, [selectedMetric, selectedModel, confidenceLevel]);

  // Fetch predictions
  const fetchPredictions = useCallback(async () => {
    setLoadingPredictions(true);
    try {
      const response = await new Promise(resolve => {
        setTimeout(() => {
          resolve({
            metric_name: selectedMetric,
            anomalies_detected: generateMockAnomalies(),
            recommendations: generateMockRecommendations(),
            risk_assessment: {
              overall_risk: 0.45,
              performance_risk: 0.50,
              operational_risk: 0.35,
              resource_risk: 0.48,
            },
            performance_score: 72.5,
          });
        }, 600);
      });

      setPredictions(response);
      setAnomalies(response.anomalies_detected || []);
      setRecommendations(response.recommendations || []);
      setPerformanceScore(response.performance_score || 0);
      setRiskScore(response.risk_assessment?.overall_risk || 0);
    } catch (error) {
      console.error('Prediction fetch error:', error);
    } finally {
      setLoadingPredictions(false);
    }
  }, [selectedMetric]);

  // Generate mock forecast points
  const generateMockForecastPoints = () => {
    const now = new Date();
    return Array.from({ length: periods }, (_, i) => ({
      timestamp: new Date(now.getTime() + (i + 1) * 24 * 60 * 60 * 1000).toLocaleDateString(),
      predicted_value: 100 + (i * 5) + Math.random() * 10,
      lower_bound: 90 + (i * 5),
      upper_bound: 110 + (i * 5),
      confidence: confidenceLevel,
    }));
  };

  // Generate mock anomalies
  const generateMockAnomalies = () => {
    return [
      {
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        observed_value: 250,
        expected_value: 100,
        severity: 0.85,
        type: 'statistical',
        confidence: 0.92,
      },
      {
        timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
        observed_value: 280,
        expected_value: 100,
        severity: 0.75,
        type: 'contextual',
        confidence: 0.88,
      },
    ];
  };

  // Generate mock recommendations
  const generateMockRecommendations = () => {
    return [
      {
        type: 'resource_allocation',
        priority: 'high',
        description: 'Increase resource allocation by 25% to handle predicted spike',
        expected_improvement: 20.0,
        confidence: 0.85,
      },
      {
        type: 'performance_optimization',
        priority: 'high',
        description: 'Optimize slow database queries',
        expected_improvement: 35.0,
        confidence: 0.80,
      },
      {
        type: 'capacity_planning',
        priority: 'medium',
        description: 'Plan infrastructure expansion for Q2',
        expected_improvement: 15.0,
        confidence: 0.75,
      },
    ];
  };

  // Initial fetch
  useEffect(() => {
    fetchForecast();
    fetchPredictions();
  }, [fetchForecast, fetchPredictions]);

  // Auto-refresh
  useEffect(() => {
    const timer = setInterval(() => {
      fetchForecast();
      fetchPredictions();
    }, refreshInterval);

    return () => clearInterval(timer);
  }, [fetchForecast, fetchPredictions, refreshInterval]);

  // Get current metric config
  const currentMetric = metrics.find(m => m.id === selectedMetric);
  const forecastData = forecasts[selectedMetric];

  const getSeverityColor = (severity) => {
    if (severity > 0.8) return '#ff4444';
    if (severity > 0.6) return '#ffaa00';
    if (severity > 0.4) return '#ffcc00';
    return '#88cc00';
  };

  const getRiskLevelColor = (score) => {
    if (score > 0.7) return '#ff4444';
    if (score > 0.4) return '#ffaa00';
    return '#88cc00';
  };

  const getRiskLevelLabel = (score) => {
    if (score > 0.7) return 'CRITICAL';
    if (score > 0.4) return 'MEDIUM';
    return 'LOW';
  };

  return (
    <div className="forecast-dashboard">
      <div className="dashboard-header">
        <h1>📊 Advanced Forecasting Dashboard</h1>
        <div className="header-controls">
          <div className="control-group">
            <label>Metric:</label>
            <select 
              value={selectedMetric} 
              onChange={(e) => setSelectedMetric(e.target.value)}
              disabled={loadingForecasts || loadingPredictions}
            >
              {metrics.map(m => (
                <option key={m.id} value={m.id}>{m.label}</option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>Model:</label>
            <select 
              value={selectedModel} 
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={loadingForecasts}
            >
              {models.map(m => (
                <option key={m.id} value={m.id}>{m.label}</option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>Periods:</label>
            <input 
              type="number" 
              min="1" 
              max="30"
              value={periods}
              onChange={(e) => setPeriods(Math.max(1, Math.min(30, parseInt(e.target.value))))}
              disabled={loadingForecasts}
            />
          </div>

          <div className="control-group">
            <label>Confidence:</label>
            <input 
              type="range" 
              min="0.8" 
              max="0.99"
              step="0.05"
              value={confidenceLevel}
              onChange={(e) => setConfidenceLevel(parseFloat(e.target.value))}
              disabled={loadingForecasts}
            />
            <span>{(confidenceLevel * 100).toFixed(0)}%</span>
          </div>

          <div className="control-group">
            <label>Refresh:</label>
            <select 
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
            >
              <option value={60000}>1 min</option>
              <option value={300000}>5 min</option>
              <option value={600000}>10 min</option>
              <option value={1800000}>30 min</option>
            </select>
          </div>

          <button 
            className="btn-refresh"
            onClick={() => {
              fetchForecast();
              fetchPredictions();
            }}
            disabled={loadingForecasts || loadingPredictions}
          >
            {loadingForecasts || loadingPredictions ? '⟳ Loading...' : '⟳ Refresh'}
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">Performance Score</div>
          <div className="kpi-value">{performanceScore.toFixed(1)}</div>
          <div className="kpi-bar">
            <div className="kpi-fill" style={{ width: `${performanceScore}%` }}></div>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Risk Level</div>
          <div className="kpi-value" style={{ color: getRiskLevelColor(riskScore) }}>
            {getRiskLevelLabel(riskScore)}
          </div>
          <div className="kpi-detail">{(riskScore * 100).toFixed(0)}% score</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Anomalies Detected</div>
          <div className="kpi-value">{anomalies.length}</div>
          <div className="kpi-detail">
            {anomalies.filter(a => a.severity > 0.7).length} high severity
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Recommendations</div>
          <div className="kpi-value">{recommendations.length}</div>
          <div className="kpi-detail">
            {recommendations.filter(r => r.priority === 'high').length} high priority
          </div>
        </div>
      </div>

      {/* View Mode Tabs */}
      <div className="view-tabs">
        <button
          className={`tab ${viewMode === 'overview' ? 'active' : ''}`}
          onClick={() => setViewMode('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${viewMode === 'detailed' ? 'active' : ''}`}
          onClick={() => setViewMode('detailed')}
        >
          Detailed Analysis
        </button>
        <button
          className={`tab ${viewMode === 'models' ? 'active' : ''}`}
          onClick={() => setViewMode('models')}
        >
          Model Comparison
        </button>
      </div>

      {/* Overview Mode */}
      {viewMode === 'overview' && (
        <div className="view-section">
          {/* Forecast Chart */}
          <div className="chart-container">
            <h2>Forecast: {currentMetric?.label}</h2>
            {forecastData && (
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={forecastData.forecast_points}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="lower_bound"
                    fill="#e8f4f8"
                    stroke="none"
                    name="Lower Bound"
                  />
                  <Line
                    type="monotone"
                    dataKey="predicted_value"
                    stroke="#1f77b4"
                    name="Prediction"
                    strokeWidth={2}
                  />
                  <Area
                    type="monotone"
                    dataKey="upper_bound"
                    fill="none"
                    stroke="#c5e1ec"
                    name="Upper Bound"
                    strokeDasharray="5 5"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            )}
            {forecastData && (
              <div className="chart-stats">
                <div className="stat">
                  <span>R² Score:</span> <strong>{forecastData.r_squared.toFixed(3)}</strong>
                </div>
                <div className="stat">
                  <span>RMSE:</span> <strong>{forecastData.rmse.toFixed(2)}</strong>
                </div>
                <div className="stat">
                  <span>MAPE:</span> <strong>{(forecastData.mape * 100).toFixed(2)}%</strong>
                </div>
                <div className="stat">
                  <span>Trend:</span> <strong>{forecastData.trend}</strong>
                </div>
              </div>
            )}
          </div>

          {/* Anomalies Section */}
          <div className="section">
            <h2>🚨 Detected Anomalies</h2>
            {anomalies.length > 0 ? (
              <div className="anomalies-list">
                {anomalies.map((anomaly, idx) => (
                  <div key={idx} className="anomaly-card">
                    <div className="anomaly-header">
                      <span className="anomaly-type">{anomaly.type}</span>
                      <div 
                        className="severity-badge"
                        style={{ backgroundColor: getSeverityColor(anomaly.severity) }}
                      >
                        {(anomaly.severity * 100).toFixed(0)}%
                      </div>
                    </div>
                    <div className="anomaly-details">
                      <div>Observed: <strong>{anomaly.observed_value.toFixed(2)}</strong></div>
                      <div>Expected: <strong>{anomaly.expected_value.toFixed(2)}</strong></div>
                      <div>Confidence: <strong>{(anomaly.confidence * 100).toFixed(0)}%</strong></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#666' }}>No anomalies detected in recent data.</p>
            )}
          </div>
        </div>
      )}

      {/* Detailed Analysis Mode */}
      {viewMode === 'detailed' && (
        <div className="view-section">
          {/* Recommendations */}
          <div className="section">
            <h2>💡 Recommendations</h2>
            {recommendations.length > 0 ? (
              <div className="recommendations-list">
                {recommendations.map((rec, idx) => (
                  <div key={idx} className={`recommendation-card priority-${rec.priority}`}>
                    <div className="rec-header">
                      <span className="rec-type">{rec.type.replace(/_/g, ' ')}</span>
                      <span className={`priority-badge ${rec.priority}`}>{rec.priority.toUpperCase()}</span>
                    </div>
                    <p className="rec-description">{rec.description}</p>
                    <div className="rec-stats">
                      <div className="stat">
                        Expected Improvement: <strong>+{rec.expected_improvement.toFixed(1)}%</strong>
                      </div>
                      <div className="stat">
                        Confidence: <strong>{(rec.confidence * 100).toFixed(0)}%</strong>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#666' }}>No recommendations available.</p>
            )}
          </div>

          {/* Risk Assessment */}
          <div className="section">
            <h2>⚠️ Risk Assessment</h2>
            {predictions && (
              <div className="risk-grid">
                {Object.entries(predictions.risk_assessment || {}).map(([key, value]) => (
                  <div key={key} className="risk-item">
                    <div className="risk-label">{key.replace(/_/g, ' ')}</div>
                    <div className="risk-bar">
                      <div 
                        className="risk-fill"
                        style={{
                          width: `${value * 100}%`,
                          backgroundColor: getRiskLevelColor(value),
                        }}
                      ></div>
                    </div>
                    <div className="risk-value">{(value * 100).toFixed(0)}%</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Model Comparison Mode */}
      {viewMode === 'models' && (
        <div className="view-section">
          <div className="section">
            <h2>Model Performance Comparison</h2>
            <div className="model-comparison-table">
              <table>
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>RMSE</th>
                    <th>MAPE</th>
                    <th>R²</th>
                    <th>Performance</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { name: 'Exponential Smoothing', rmse: 10.2, mape: 0.07, r2: 0.94 },
                    { name: 'Linear Regression', rmse: 12.5, mape: 0.08, r2: 0.92 },
                    { name: 'Moving Average', rmse: 8.5, mape: 0.06, r2: 0.88 },
                    { name: 'Polynomial', rmse: 9.8, mape: 0.065, r2: 0.91 },
                  ].map((model, idx) => (
                    <tr key={idx} className={model.r2 > 0.92 ? 'best-model' : ''}>
                      <td>{model.name}</td>
                      <td>{model.rmse.toFixed(2)}</td>
                      <td>{(model.mape * 100).toFixed(2)}%</td>
                      <td>{model.r2.toFixed(3)}</td>
                      <td>
                        <div className="performance-bar">
                          <div 
                            className="performance-fill"
                            style={{ width: `${model.r2 * 100}%` }}
                          ></div>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Loading States */}
      {(loadingForecasts || loadingPredictions) && (
        <div className="loading-overlay">
          <div className="spinner">⟳</div>
          <p>Analyzing forecasts and predictions...</p>
        </div>
      )}
    </div>
  );
};

export default ForecastDashboard;
