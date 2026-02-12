import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart, Line, ScatterChart, Scatter, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ComposedChart, Area
} from 'recharts';
import './PredictionViewer.css';

const PredictionViewer = ({ workspaceId, metricName = 'execution_time' }) => {
  const [predictionData, setPredictionData] = useState(null);
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [selectedRecommendation, setSelectedRecommendation] = useState(null);
  const [loadingData, setLoadingData] = useState(false);
  const [viewMode, setViewMode] = useState('summary'); // summary, anomalies, recommendations, risks
  const [timeRange, setTimeRange] = useState('7d'); // 7d, 30d, 90d
  const [analysisDepth, setAnalysisDepth] = useState('standard'); // quick, standard, deep
  const [expandedAnomalies, setExpandedAnomalies] = useState(new Set());
  const [chartData, setChartData] = useState([]);

  // Fetch prediction data
  const fetchPredictionData = useCallback(async () => {
    setLoadingData(true);
    try {
      // Mock API call
      const response = await new Promise(resolve => {
        setTimeout(() => {
          resolve({
            metric_name: metricName,
            analysis_timestamp: new Date().toISOString(),
            summary: {
              status: 'Concerning Trends',
              confidence: 0.88,
              last_analyzed: new Date(Date.now() - 300000).toISOString(),
            },
            anomalies: [
              {
                id: 'anom_1',
                timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
                type: 'statistical',
                severity: 0.85,
                confidence: 0.92,
                observed: 250,
                expected: 100,
                std_deviations: 3.1,
                description: 'Execution time spike detected',
                context: metricName,
                affected_entities: ['agent_1', 'agent_3'],
                duration_minutes: 45,
                recovery_expected: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
                impact: 'Critical',
              },
              {
                id: 'anom_2',
                timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
                type: 'trend_break',
                severity: 0.72,
                confidence: 0.84,
                observed: 180,
                expected: 100,
                std_deviations: 2.4,
                description: 'Trend direction reversed',
                context: metricName,
                affected_entities: ['task_batch_2'],
                duration_minutes: 120,
                recovery_expected: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
                impact: 'High',
              },
              {
                id: 'anom_3',
                timestamp: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
                type: 'contextual',
                severity: 0.55,
                confidence: 0.78,
                observed: 140,
                expected: 100,
                std_deviations: 1.8,
                description: 'Value outside expected context range',
                context: metricName,
                affected_entities: ['service_api'],
                duration_minutes: 30,
                recovery_expected: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
                impact: 'Medium',
              },
            ],
            recommendations: [
              {
                id: 'rec_1',
                type: 'performance_optimization',
                priority: 'high',
                title: 'Optimize Query Performance',
                description: 'Database queries are taking 3x longer than baseline. Implement caching for frequently accessed data.',
                expected_impact: '+35% improvement',
                confidence: 0.85,
                estimated_effort_hours: 4,
                actions: [
                  'Add Redis caching layer',
                  'Implement query result pagination',
                  'Add database indices for common queries',
                  'Review slow query logs',
                ],
                dependencies: [],
                affected_components: ['DatabaseService', 'CacheLayer'],
              },
              {
                id: 'rec_2',
                type: 'resource_allocation',
                priority: 'high',
                title: 'Scale Resource Allocation',
                description: 'Current resource allocation is insufficient for predicted load increase.',
                expected_impact: '+25% throughput',
                confidence: 0.82,
                estimated_effort_hours: 2,
                actions: [
                  'Increase CPU allocation by 30%',
                  'Increase memory by 40%',
                  'Enable auto-scaling rules',
                ],
                dependencies: ['performance_optimization'],
                affected_components: ['Container', 'OrchestrationEngine'],
              },
              {
                id: 'rec_3',
                type: 'capacity_planning',
                priority: 'medium',
                title: 'Plan Infrastructure Expansion',
                description: 'Growth trends suggest need for infrastructure expansion in Q2.',
                expected_impact: '+50% capacity',
                confidence: 0.75,
                estimated_effort_hours: 16,
                actions: [
                  'Analyze growth trends',
                  'Plan new deployments',
                  'Estimate costs',
                  'Create implementation timeline',
                ],
                dependencies: [],
                affected_components: ['InfrastructureManagement'],
              },
            ],
            risk_assessment: {
              overall_risk: 0.52,
              performance_risk: 0.68,
              operational_risk: 0.42,
              resource_risk: 0.51,
              trend_risk: 0.55,
              details: {
                performance: {
                  current: 0.68,
                  trend: 'increasing',
                  forecast_24h: 0.72,
                },
                operational: {
                  current: 0.42,
                  trend: 'stable',
                  forecast_24h: 0.43,
                },
              },
            },
            performance_metrics: {
              score: 72.5,
              trend: 'declining',
              change_24h: -2.5,
              outliers: 3,
              forecast_7d: 68.0,
            },
          });
        }, 800);
      });

      setPredictionData(response);
      
      // Generate chart data
      const data = Array.from({ length: 24 }, (_, i) => ({
        hour: `${i}:00`,
        predicted: 100 + Math.random() * 50 + (i % 4) * 20,
        anomaly: Math.random() > 0.8 ? 150 + Math.random() * 100 : null,
      }));
      setChartData(data);
    } catch (error) {
      console.error('Prediction fetch error:', error);
    } finally {
      setLoadingData(false);
    }
  }, [metricName]);

  // Initial fetch
  useEffect(() => {
    fetchPredictionData();
  }, [fetchPredictionData]);

  // Toggle anomaly expansion
  const toggleAnomalyExpansion = (anomalyId) => {
    setExpandedAnomalies(prev => {
      const newSet = new Set(prev);
      if (newSet.has(anomalyId)) {
        newSet.delete(anomalyId);
      } else {
        newSet.add(anomalyId);
      }
      return newSet;
    });
  };

  const getSeverityColor = (severity) => {
    if (severity > 0.8) return '#d9534f';
    if (severity > 0.6) return '#f0ad4e';
    if (severity > 0.4) return '#f0ad4e';
    return '#5cb85c';
  };

  const getSeverityLabel = (severity) => {
    if (severity > 0.8) return 'CRITICAL';
    if (severity > 0.6) return 'HIGH';
    if (severity > 0.4) return 'MEDIUM';
    return 'LOW';
  };

  const getPriorityColor = (priority) => {
    if (priority === 'critical') return '#d9534f';
    if (priority === 'high') return '#f0ad4e';
    if (priority === 'medium') return '#5bc0de';
    return '#5cb85c';
  };

  const getRiskColor = (risk) => {
    if (risk > 0.7) return '#d9534f';
    if (risk > 0.4) return '#f0ad4e';
    return '#5cb85c';
  };

  return (
    <div className="prediction-viewer">
      <div className="viewer-header">
        <h1>🔮 Prediction Analysis: {metricName}</h1>
        <div className="header-actions">
          <div className="control-group">
            <label>Time Range:</label>
            <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
            </select>
          </div>

          <div className="control-group">
            <label>Analysis Depth:</label>
            <select 
              value={analysisDepth} 
              onChange={(e) => setAnalysisDepth(e.target.value)}
            >
              <option value="quick">Quick (1 min)</option>
              <option value="standard">Standard (3 min)</option>
              <option value="deep">Deep (10 min)</option>
            </select>
          </div>

          <button 
            className="btn-refresh"
            onClick={fetchPredictionData}
            disabled={loadingData}
          >
            {loadingData ? '⟳ Analyzing...' : '⟳ Refresh'}
          </button>
        </div>
      </div>

      {/* KPI Summary Cards */}
      {predictionData && (
        <div className="kpi-summary">
          <div className="kpi-card highlight">
            <div className="kpi-label">Performance Score</div>
            <div className="kpi-large-value">{predictionData.performance_metrics.score.toFixed(1)}</div>
            <div className={`kpi-trend ${predictionData.performance_metrics.trend}`}>
              {predictionData.performance_metrics.trend === 'declining' ? '↓' : '↑'} 
              {Math.abs(predictionData.performance_metrics.change_24h).toFixed(1)}% in 24h
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-label">Anomalies</div>
            <div className="kpi-large-value">{predictionData.anomalies.length}</div>
            <div className="kpi-detail">
              {predictionData.anomalies.filter(a => a.severity > 0.7).length} Critical
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-label">Overall Risk</div>
            <div className="kpi-large-value" style={{ color: getRiskColor(predictionData.risk_assessment.overall_risk) }}>
              {(predictionData.risk_assessment.overall_risk * 100).toFixed(0)}%
            </div>
            <div className="kpi-detail">risk score</div>
          </div>

          <div className="kpi-card">
            <div className="kpi-label">Actions Needed</div>
            <div className="kpi-large-value">{predictionData.recommendations.length}</div>
            <div className="kpi-detail">
              {predictionData.recommendations.filter(r => r.priority === 'high').length} High Priority
            </div>
          </div>
        </div>
      )}

      {/* View Mode Navigation */}
      <div className="view-navigation">
        <button 
          className={`nav-btn ${viewMode === 'summary' ? 'active' : ''}`}
          onClick={() => setViewMode('summary')}
        >
          Summary
        </button>
        <button 
          className={`nav-btn ${viewMode === 'anomalies' ? 'active' : ''}`}
          onClick={() => setViewMode('anomalies')}
        >
          Anomalies ({predictionData?.anomalies.length || 0})
        </button>
        <button 
          className={`nav-btn ${viewMode === 'recommendations' ? 'active' : ''}`}
          onClick={() => setViewMode('recommendations')}
        >
          Recommendations ({predictionData?.recommendations.length || 0})
        </button>
        <button 
          className={`nav-btn ${viewMode === 'risks' ? 'active' : ''}`}
          onClick={() => setViewMode('risks')}
        >
          Risk Analysis
        </button>
      </div>

      {/* Summary View */}
      {viewMode === 'summary' && predictionData && (
        <div className="view-content">
          {/* Prediction Chart */}
          <div className="chart-section">
            <h2>24-Hour Prediction</h2>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="predicted" 
                  stroke="#1f77b4"
                  name="Predicted Value"
                  strokeWidth={2}
                />
                <Scatter 
                  dataKey="anomaly" 
                  fill="#d9534f"
                  name="Detected Anomalies"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Top Issues */}
          <div className="section">
            <h2>⚠️ Top Issues</h2>
            <div className="issues-list">
              {predictionData.anomalies.slice(0, 3).map(anomaly => (
                <div key={anomaly.id} className="issue-card">
                  <div className="issue-header">
                    <span className={`severity-badge ${anomaly.type}`}>
                      {getSeverityLabel(anomaly.severity)}
                    </span>
                    <span className="issue-type">{anomaly.type}</span>
                    <span className="issue-time">
                      {new Date(anomaly.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="issue-description">{anomaly.description}</p>
                  <div className="issue-details">
                    <span>Observed: {anomaly.observed.toFixed(2)}</span>
                    <span>Expected: {anomaly.expected.toFixed(2)}</span>
                    <span>Confidence: {(anomaly.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recommended Actions */}
          <div className="section">
            <h2>✓ Recommended Actions</h2>
            <div className="quick-actions">
              {predictionData.recommendations.slice(0, 2).map(rec => (
                <div key={rec.id} className="action-card" style={{ borderLeftColor: getPriorityColor(rec.priority) }}>
                  <div className="action-header">
                    <span className="action-title">{rec.title}</span>
                    <span className={`priority-badge ${rec.priority}`}>{rec.priority.toUpperCase()}</span>
                  </div>
                  <p>{rec.description}</p>
                  <div className="action-impact">Expected: {rec.expected_impact}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Anomalies View */}
      {viewMode === 'anomalies' && predictionData && (
        <div className="view-content">
          <div className="section">
            <h2>Detailed Anomaly Analysis</h2>
            <div className="anomalies-detailed">
              {predictionData.anomalies.map(anomaly => (
                <div key={anomaly.id} className="anomaly-detail-card">
                  <div 
                    className="anomaly-header-expandable"
                    onClick={() => toggleAnomalyExpansion(anomaly.id)}
                  >
                    <div className="header-left">
                      <span 
                        className="severity-dot"
                        style={{ backgroundColor: getSeverityColor(anomaly.severity) }}
                      ></span>
                      <div className="header-info">
                        <h3>{anomaly.description}</h3>
                        <p>{new Date(anomaly.timestamp).toLocaleString()}</p>
                      </div>
                    </div>
                    <div className="header-right">
                      <span className="impact-badge">{anomaly.impact}</span>
                      <span className="expand-icon">
                        {expandedAnomalies.has(anomaly.id) ? '▼' : '▶'}
                      </span>
                    </div>
                  </div>

                  {expandedAnomalies.has(anomaly.id) && (
                    <div className="anomaly-details-expanded">
                      <div className="detail-grid">
                        <div className="detail-item">
                          <label>Type:</label>
                          <span>{anomaly.type}</span>
                        </div>
                        <div className="detail-item">
                          <label>Severity:</label>
                          <span>{getSeverityLabel(anomaly.severity)} ({(anomaly.severity * 100).toFixed(0)}%)</span>
                        </div>
                        <div className="detail-item">
                          <label>Confidence:</label>
                          <span>{(anomaly.confidence * 100).toFixed(0)}%</span>
                        </div>
                        <div className="detail-item">
                          <label>Duration:</label>
                          <span>{anomaly.duration_minutes} minutes</span>
                        </div>
                        <div className="detail-item">
                          <label>Std Deviations:</label>
                          <span>{anomaly.std_deviations.toFixed(2)}σ</span>
                        </div>
                        <div className="detail-item">
                          <label>Recovery Expected:</label>
                          <span>{new Date(anomaly.recovery_expected).toLocaleTimeString()}</span>
                        </div>
                      </div>
                      <div className="affected-entities">
                        <h4>Affected Entities:</h4>
                        <div className="entity-tags">
                          {anomaly.affected_entities.map(entity => (
                            <span key={entity} className="entity-tag">{entity}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Recommendations View */}
      {viewMode === 'recommendations' && predictionData && (
        <div className="view-content">
          <div className="section">
            <h2>Action Plan</h2>
            {predictionData.recommendations.map(rec => (
              <div 
                key={rec.id} 
                className="recommendation-detail"
                onClick={() => setSelectedRecommendation(
                  selectedRecommendation?.id === rec.id ? null : rec
                )}
              >
                <div className="rec-header-main">
                  <div className="rec-title-group">
                    <h3>{rec.title}</h3>
                    <span className={`priority-badge ${rec.priority}`}>{rec.priority.toUpperCase()}</span>
                  </div>
                  <div className="rec-metrics">
                    <span className="metric">Impact: {rec.expected_impact}</span>
                    <span className="metric">Confidence: {(rec.confidence * 100).toFixed(0)}%</span>
                    <span className="metric">Effort: ~{rec.estimated_effort_hours}h</span>
                  </div>
                </div>

                <p className="rec-description">{rec.description}</p>

                {selectedRecommendation?.id === rec.id && (
                  <div className="rec-details-expanded">
                    <div className="actions-list">
                      <h4>Action Items:</h4>
                      <ul>
                        {rec.actions.map((action, idx) => (
                          <li key={idx}>{action}</li>
                        ))}
                      </ul>
                    </div>
                    {rec.affected_components.length > 0 && (
                      <div className="components-affected">
                        <h4>Affected Components:</h4>
                        <div className="component-tags">
                          {rec.affected_components.map(comp => (
                            <span key={comp} className="component-tag">{comp}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Analysis View */}
      {viewMode === 'risks' && predictionData && (
        <div className="view-content">
          <div className="section">
            <h2>Risk Assessment</h2>
            <div className="risk-heatmap">
              {Object.entries(predictionData.risk_assessment.details || {}).map(([key, value]) => (
                <div key={key} className="risk-item-detailed">
                  <div className="risk-label">{key}</div>
                  <div className="risk-values">
                    <span className="value-label">Current:</span>
                    <span 
                      className="value-score"
                      style={{ color: getRiskColor(value.current) }}
                    >
                      {(value.current * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="risk-values">
                    <span className="value-label">Trend:</span>
                    <span className="value-trend">{value.trend}</span>
                  </div>
                  <div className="risk-values">
                    <span className="value-label">24h Forecast:</span>
                    <span 
                      className="value-forecast"
                      style={{ color: getRiskColor(value.forecast_24h) }}
                    >
                      {(value.forecast_24h * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loadingData && (
        <div className="loading-overlay">
          <div className="spinner">⟳</div>
          <p>Analyzing predictions and generating insights...</p>
        </div>
      )}
    </div>
  );
};

export default PredictionViewer;
