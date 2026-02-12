import React, { useState, useEffect, useCallback } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import './AdvancedMLDashboard.css';

const AdvancedMLDashboard = ({ workspaceId, refreshInterval = 5000 }) => {
  const [predictions, setPredictions] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [healthScore, setHealthScore] = useState(0);
  const [modelPerformance, setModelPerformance] = useState({});
  const [automationStatus, setAutomationStatus] = useState({});
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedMetric, setSelectedMetric] = useState('cpu_utilization');

  // Fetch predictions
  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const response = await fetch('/api/v1/ml_advanced/predictions/batch', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Workspace-ID': workspaceId,
          },
          body: JSON.stringify({
            metrics: ['cpu_utilization', 'memory_utilization', 'cost'],
            forecast_hours: 168,
          }),
        });
        const data = await response.json();
        if (data.success) {
          setPredictions(data.predictions);
        }
      } catch (error) {
        console.error('Failed to fetch predictions:', error);
      }
    };

    fetchPredictions();
    const interval = setInterval(fetchPredictions, refreshInterval);
    return () => clearInterval(interval);
  }, [workspaceId, refreshInterval]);

  // Fetch anomalies
  useEffect(() => {
    const fetchAnomalies = async () => {
      try {
        const response = await fetch(
          `/api/v1/ml_advanced/anomalies/history?lookback_days=30`,
          {
            headers: { 'X-Workspace-ID': workspaceId },
          }
        );
        const data = await response.json();
        if (data.success) {
          setAnomalies(data.anomalies);
        }
      } catch (error) {
        console.error('Failed to fetch anomalies:', error);
      }
    };

    fetchAnomalies();
    const interval = setInterval(fetchAnomalies, refreshInterval);
    return () => clearInterval(interval);
  }, [workspaceId, refreshInterval]);

  // Fetch health score
  useEffect(() => {
    const fetchHealthScore = async () => {
      try {
        const response = await fetch('/api/v1/ml_advanced/anomalies/health-score', {
          headers: { 'X-Workspace-ID': workspaceId },
        });
        const data = await response.json();
        if (data.success) {
          setHealthScore(data.health);
        }
      } catch (error) {
        console.error('Failed to fetch health score:', error);
      }
    };

    fetchHealthScore();
    const interval = setInterval(fetchHealthScore, refreshInterval);
    return () => clearInterval(interval);
  }, [workspaceId, refreshInterval]);

  // Fetch model performance
  useEffect(() => {
    const fetchModelPerformance = async () => {
      try {
        const response = await fetch(
          '/api/v1/ml_advanced/predictions/model-performance?model_type=ensemble',
          {
            headers: { 'X-Workspace-ID': workspaceId },
          }
        );
        const data = await response.json();
        if (data.success) {
          setModelPerformance(data.model);
        }
      } catch (error) {
        console.error('Failed to fetch model performance:', error);
      }
    };

    fetchModelPerformance();
  }, [workspaceId]);

  // Fetch insights
  useEffect(() => {
    const fetchInsights = async () => {
      try {
        const response = await fetch('/api/v1/ml_advanced/insights/actionable', {
          headers: { 'X-Workspace-ID': workspaceId },
        });
        const data = await response.json();
        if (data.success) {
          setInsights(data.insights);
          setLoading(false);
        }
      } catch (error) {
        console.error('Failed to fetch insights:', error);
        setLoading(false);
      }
    };

    fetchInsights();
    const interval = setInterval(fetchInsights, refreshInterval);
    return () => clearInterval(interval);
  }, [workspaceId, refreshInterval]);

  // KPI Cards
  const KPICard = ({ title, value, unit, trend, status }) => (
    <div className={`kpi-card ${status}`}>
      <div className="kpi-header">{title}</div>
      <div className="kpi-value">{value}{unit}</div>
      <div className={`kpi-trend ${trend}`}>{trend === 'up' ? '↑' : '↓'}</div>
    </div>
  );

  // Prediction Chart
  const PredictionChart = () => {
    const data = predictions.map((p) => ({
      name: p.metric.split('_')[0],
      predicted_value: p.predicted_value,
      confidence: p.confidence * 100,
    }));

    return (
      <div className="chart-container">
        <h3>Metric Predictions (168 hours)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="predicted_value" fill="#8884d8" />
            <Bar dataKey="confidence" fill="#82ca9d" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  // Anomaly Severity Distribution
  const AnomalySeverityChart = () => {
    const severityCounts = {
      critical: anomalies.filter((a) => a.severity === 'critical').length,
      high: anomalies.filter((a) => a.severity === 'high').length,
      medium: anomalies.filter((a) => a.severity === 'medium').length,
      low: anomalies.filter((a) => a.severity === 'low').length,
    };

    const data = [
      { name: 'Critical', value: severityCounts.critical, fill: '#ef4444' },
      { name: 'High', value: severityCounts.high, fill: '#f97316' },
      { name: 'Medium', value: severityCounts.medium, fill: '#eab308' },
      { name: 'Low', value: severityCounts.low, fill: '#22c55e' },
    ];

    return (
      <div className="chart-container">
        <h3>Anomaly Severity Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, value }) => `${name}: ${value}`}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  };

  // Model Performance Metrics
  const ModelPerformanceCard = () => (
    <div className="model-performance-card">
      <h3>ML Model Performance</h3>
      <div className="metrics-grid">
        <div className="metric">
          <span className="metric-label">Accuracy</span>
          <span className="metric-value">{(modelPerformance.accuracy * 100).toFixed(1)}%</span>
        </div>
        <div className="metric">
          <span className="metric-label">Precision</span>
          <span className="metric-value">{(modelPerformance.precision * 100).toFixed(1)}%</span>
        </div>
        <div className="metric">
          <span className="metric-label">Recall</span>
          <span className="metric-value">{(modelPerformance.recall * 100).toFixed(1)}%</span>
        </div>
        <div className="metric">
          <span className="metric-label">MAPE</span>
          <span className="metric-value">{modelPerformance.mape?.toFixed(2)}%</span>
        </div>
      </div>
    </div>
  );

  // Health Score Gauge
  const HealthScoreGauge = () => {
    const score = healthScore.score || 0;
    const status = healthScore.status || 'unknown';
    const statusColor = {
      healthy: '#22c55e',
      degraded: '#eab308',
      critical: '#ef4444',
      unknown: '#6b7280',
    };

    return (
      <div className="health-score-gauge">
        <div className="gauge-circle" style={{ '--score': score, '--color': statusColor[status] }}>
          <div className="gauge-value">{score.toFixed(1)}</div>
          <div className="gauge-label">Health Score</div>
        </div>
        <div className="health-details">
          <div className="detail-row">
            <span>Status:</span>
            <span className={`badge ${status}`}>{status.toUpperCase()}</span>
          </div>
          <div className="detail-row">
            <span>Trend:</span>
            <span>{healthScore.trend}</span>
          </div>
          <div className="detail-row">
            <span>Critical Anomalies:</span>
            <span className="critical">{healthScore.critical_anomalies}</span>
          </div>
        </div>
      </div>
    );
  };

  // Recommendations List
  const RecommendationsSection = () => (
    <div className="recommendations-section">
      <h3>Recommended Actions</h3>
      <div className="recommendations-list">
        {insights.recommended_actions?.slice(0, 5).map((action, index) => (
          <div key={index} className="recommendation-item">
            <div className="recommendation-header">
              <span className="action-type">{action.action_type}</span>
              <span className={`risk-level ${action.risk_level}`}>{action.risk_level}</span>
            </div>
            <p className="description">{action.description}</p>
            <div className="impact">
              Estimated Impact: <strong>${action.estimated_impact.toFixed(2)}/month</strong>
            </div>
            {action.auto_approved && <span className="auto-approved badge">Auto-Approved</span>}
          </div>
        ))}
      </div>
    </div>
  );

  if (loading) {
    return <div className="loading">Loading Advanced ML Dashboard...</div>;
  }

  return (
    <div className="advanced-ml-dashboard">
      <h1>Advanced ML Analytics</h1>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <KPICard
          title="Health Score"
          value={healthScore.score || 0}
          unit="/100"
          trend={healthScore.trend === 'improving' ? 'up' : 'down'}
          status={healthScore.status}
        />
        <KPICard
          title="Anomalies"
          value={healthScore.anomalies_detected || 0}
          unit=""
          trend="neutral"
          status="info"
        />
        <KPICard
          title="Critical Issues"
          value={healthScore.critical_anomalies || 0}
          unit=""
          trend="down"
          status="critical"
        />
        <KPICard
          title="Model Accuracy"
          value={(modelPerformance.accuracy * 100).toFixed(1)}
          unit="%"
          trend="up"
          status="success"
        />
      </div>

      {/* Tab Navigation */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${activeTab === 'predictions' ? 'active' : ''}`}
          onClick={() => setActiveTab('predictions')}
        >
          Predictions
        </button>
        <button
          className={`tab ${activeTab === 'anomalies' ? 'active' : ''}`}
          onClick={() => setActiveTab('anomalies')}
        >
          Anomalies
        </button>
        <button
          className={`tab ${activeTab === 'recommendations' ? 'active' : ''}`}
          onClick={() => setActiveTab('recommendations')}
        >
          Recommendations
        </button>
      </div>

      {/* Content */}
      <div className="tab-content">
        {activeTab === 'overview' && (
          <div className="overview-section">
            <div className="row">
              <HealthScoreGauge />
              <ModelPerformanceCard />
            </div>
            <PredictionChart />
          </div>
        )}

        {activeTab === 'predictions' && (
          <div className="predictions-section">
            <PredictionChart />
            <div className="predictions-table">
              <h3>Detailed Predictions</h3>
              <table>
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th>Predicted Value</th>
                    <th>Confidence</th>
                    <th>Level</th>
                  </tr>
                </thead>
                <tbody>
                  {predictions.map((p, idx) => (
                    <tr key={idx}>
                      <td>{p.metric}</td>
                      <td>{p.predicted_value.toFixed(2)}</td>
                      <td>{(p.confidence * 100).toFixed(1)}%</td>
                      <td>{p.confidence_level}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'anomalies' && (
          <div className="anomalies-section">
            <AnomalySeverityChart />
            <div className="anomalies-timeline">
              <h3>Recent Anomalies</h3>
              <div className="timeline">
                {anomalies.slice(0, 10).map((a, idx) => (
                  <div key={idx} className={`timeline-item ${a.severity}`}>
                    <div className="timeline-marker" />
                    <div className="timeline-content">
                      <div className="timeline-title">{a.metrics[0]}</div>
                      <div className="timeline-subtitle">
                        Impact Score: <strong>{a.impact_score}</strong>
                      </div>
                      <div className="timeline-time">
                        {new Date(a.detected_at).toLocaleString()}
                      </div>
                    </div>
                    <span className={`severity-badge ${a.severity}`}>{a.severity}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'recommendations' && (
          <div className="recommendations-section">
            <RecommendationsSection />
          </div>
        )}
      </div>
    </div>
  );
};

export default AdvancedMLDashboard;
