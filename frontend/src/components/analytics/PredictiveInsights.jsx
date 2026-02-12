/**
 * Phase 25: Predictive Insights Component
 * Forecasts, anomaly detection, trend visualization
 */

import React, { useState, useEffect, useCallback } from 'react';

const PredictiveInsights = ({ apiBaseUrl = 'http://localhost:5000' }) => {
  // Prediction state
  const [selectedMetric, setSelectedMetric] = useState(null);
  const [metrics, setMetrics] = useState([]);
  const [forecastData, setForecastData] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // View state
  const [viewMode, setViewMode] = useState('forecast'); // forecast, anomalies, insights
  const [selectedForecastId, setSelectedForecastId] = useState(null);
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  
  // Prediction models
  const [models, setModels] = useState({});
  const [modelAccuracy, setModelAccuracy] = useState({});
  
  // Filters
  const [severityFilter, setSeverityFilter] = useState('all');
  const [timeHorizon, setTimeHorizon] = useState(7);


  // ========================================================================
  // LIFECYCLE
  // ========================================================================

  useEffect(() => {
    loadMetrics();
  }, []);

  useEffect(() => {
    if (selectedMetric) {
      runForecast();
      detectAnomalies();
      loadInsights();
    }
  }, [selectedMetric]);


  // ========================================================================
  // DATA LOADING
  // ========================================================================

  const loadMetrics = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiBaseUrl}/api/v1/analytics/metrics`);
      const data = await response.json();
      setMetrics(data.metrics || []);
      if (data.metrics && data.metrics.length > 0) {
        setSelectedMetric(data.metrics[0].metric_id);
      }
    } catch (error) {
      console.error('Failed to load metrics:', error);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);


  // ========================================================================
  // FORECASTING
  // ========================================================================

  const runForecast = useCallback(async () => {
    if (!selectedMetric) return;
    
    try {
      setLoading(true);
      
      const response = await fetch(
        `${apiBaseUrl}/api/v1/analytics/predictions/forecast?metric_id=${selectedMetric}&days=${timeHorizon}`
      );
      const data = await response.json();
      setForecastData(data);
      setSelectedForecastId(data.forecast_id);
      
      // Load model accuracy
      const accuracyResponse = await fetch(
        `${apiBaseUrl}/api/v1/analytics/predictions/${data.forecast_id}/accuracy`
      );
      const accuracyData = await accuracyResponse.json();
      setModelAccuracy(accuracyData);
      
    } catch (error) {
      console.error('Forecast failed:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedMetric, timeHorizon, apiBaseUrl]);

  const predictTrend = useCallback(async () => {
    if (!selectedMetric) return;
    
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/analytics/predictions/${selectedMetric}/trend`
      );
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Trend prediction failed:', error);
      return null;
    }
  }, [selectedMetric, apiBaseUrl]);

  const predictRevenue = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/analytics/predictions/revenue`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Revenue prediction failed:', error);
      return null;
    }
  }, [apiBaseUrl]);


  // ========================================================================
  // ANOMALY DETECTION
  // ========================================================================

  const detectAnomalies = useCallback(async () => {
    if (!selectedMetric) return;
    
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/analytics/anomalies/${selectedMetric}/detect`
      );
      const data = await response.json();
      setAnomalies(data.anomalies || []);
    } catch (error) {
      console.error('Anomaly detection failed:', error);
    }
  }, [selectedMetric, apiBaseUrl]);

  const analyzeAnomaly = useCallback(async (anomalyId) => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/analytics/anomalies/${anomalyId}/analyze`
      );
      const data = await response.json();
      setSelectedAnomaly(data);
      return data;
    } catch (error) {
      console.error('Anomaly analysis failed:', error);
      return null;
    }
  }, [apiBaseUrl]);


  // ========================================================================
  // INSIGHTS
  // ========================================================================

  const loadInsights = useCallback(async () => {
    if (!selectedMetric) return;
    
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/analytics/insights`);
      const data = await response.json();
      
      const filtered = data.insights.filter(insight => {
        if (severityFilter === 'all') return true;
        return insight.severity === severityFilter;
      });
      
      setInsights(filtered);
    } catch (error) {
      console.error('Failed to load insights:', error);
    }
  }, [selectedMetric, severityFilter, apiBaseUrl]);

  const generateInsights = useCallback(async () => {
    if (!selectedMetric) return;
    
    try {
      setLoading(true);
      const response = await fetch(`${apiBaseUrl}/api/v1/analytics/insights/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metric_id: selectedMetric })
      });
      
      const data = await response.json();
      setInsights(data.insights || []);
      
    } catch (error) {
      console.error('Insight generation failed:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedMetric, apiBaseUrl]);

  const markInsightAsRead = useCallback(async (insightId) => {
    try {
      await fetch(`${apiBaseUrl}/api/v1/analytics/insights/${insightId}/read`, {
        method: 'POST'
      });
      
      setInsights(prev => prev.map(i => 
        i.insight_id === insightId ? { ...i, read: true } : i
      ));
    } catch (error) {
      console.error('Failed to mark insight as read:', error);
    }
  }, [apiBaseUrl]);

  const getRecommendations = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/analytics/insights/recommendations`);
      const data = await response.json();
      return data.recommendations;
    } catch (error) {
      console.error('Failed to get recommendations:', error);
      return [];
    }
  }, [apiBaseUrl]);


  // ========================================================================
  // SEVERITY STYLING
  // ========================================================================

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return '#d32f2f';
      case 'warning': return '#f57c00';
      case 'info': return '#1976d2';
      default: return '#666';
    }
  };

  const getSeverityBgColor = (severity) => {
    switch (severity) {
      case 'critical': return '#ffebee';
      case 'warning': return '#fff3e0';
      case 'info': return '#e3f2fd';
      default: return '#f5f5f5';
    }
  };

  const getAnomalyTypeIcon = (type) => {
    switch (type) {
      case 'spike': return '📈';
      case 'dip': return '📉';
      case 'trend_change': return '🔄';
      case 'seasonality_break': return '⚡';
      case 'outlier': return '⚠️';
      default: return '🔔';
    }
  };


  // ========================================================================
  // RENDER FORECAST
  // ========================================================================

  const renderForecast = () => {
    if (!forecastData) {
      return <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
        No forecast data available
      </div>;
    }

    return (
      <div style={{ padding: '20px' }}>
        <h3>{forecastData.metric_name} - {timeHorizon} Day Forecast</h3>
        
        {/* Summary Stats */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr 1fr 1fr',
          gap: '15px',
          marginBottom: '20px'
        }}>
          <div style={{ backgroundColor: '#f0f0f0', padding: '15px', borderRadius: '8px' }}>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
              Forecast Value
            </div>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
              {forecastData.forecasted_value?.toFixed(2) || 'N/A'}
            </div>
          </div>
          
          <div style={{ backgroundColor: '#f0f0f0', padding: '15px', borderRadius: '8px' }}>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
              Confidence (95%)
            </div>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
              ±{forecastData.confidence_interval?.toFixed(2) || 'N/A'}
            </div>
          </div>
          
          <div style={{ backgroundColor: '#f0f0f0', padding: '15px', borderRadius: '8px' }}>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
              Model Used
            </div>
            <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
              {forecastData.model || 'Ensemble'}
            </div>
          </div>
          
          <div style={{ backgroundColor: '#f0f0f0', padding: '15px', borderRadius: '8px' }}>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
              Trend
            </div>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
              {forecastData.trend === 'increasing' ? '📈' : forecastData.trend === 'decreasing' ? '📉' : '➡️'}
            </div>
          </div>
        </div>

        {/* Forecast Points */}
        <div style={{ marginBottom: '20px' }}>
          <h4>Forecast Points</h4>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f5f5f5' }}>
                <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Day</th>
                <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Forecast</th>
                <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Lower Bound</th>
                <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Upper Bound</th>
              </tr>
            </thead>
            <tbody>
              {forecastData.forecast_points?.slice(0, 10).map((point, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '10px' }}>+{idx + 1} days</td>
                  <td style={{ padding: '10px', fontWeight: 'bold' }}>{point.value.toFixed(2)}</td>
                  <td style={{ padding: '10px', color: '#999' }}>{point.lower_bound.toFixed(2)}</td>
                  <td style={{ padding: '10px', color: '#999' }}>{point.upper_bound.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Model Accuracy */}
        {modelAccuracy.models && (
          <div style={{ marginBottom: '20px' }}>
            <h4>Model Accuracy (MAPE)</h4>
            <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
              {modelAccuracy.models.map((model, idx) => (
                <div key={idx} style={{ flex: '1', minWidth: '150px' }}>
                  <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
                    {model.name}
                  </div>
                  <div style={{
                    width: '100%',
                    height: '20px',
                    backgroundColor: '#eee',
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${(1 - model.mape) * 100}%`,
                      height: '100%',
                      backgroundColor: '#4caf50'
                    }} />
                  </div>
                  <div style={{ fontSize: '12px', marginTop: '3px' }}>
                    {(100 - model.mape * 100).toFixed(1)}% accurate
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };


  // ========================================================================
  // RENDER ANOMALIES
  // ========================================================================

  const renderAnomalies = () => {
    if (anomalies.length === 0) {
      return <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
        No anomalies detected
      </div>;
    }

    return (
      <div style={{ padding: '20px' }}>
        <h3>Anomalies Detected ({anomalies.length})</h3>
        
        {anomalies.map(anomaly => (
          <div
            key={anomaly.anomaly_id}
            onClick={() => analyzeAnomaly(anomaly.anomaly_id)}
            style={{
              backgroundColor: getSeverityBgColor(anomaly.severity),
              border: `2px solid ${getSeverityColor(anomaly.severity)}`,
              borderRadius: '8px',
              padding: '15px',
              marginBottom: '10px',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.01)'}
            onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{
                  fontSize: '18px',
                  fontWeight: 'bold',
                  color: getSeverityColor(anomaly.severity),
                  marginBottom: '5px'
                }}>
                  {getAnomalyTypeIcon(anomaly.type)} {anomaly.type.toUpperCase()}
                </div>
                <div style={{ color: '#666', fontSize: '12px', marginBottom: '5px' }}>
                  {anomaly.description}
                </div>
                <div style={{ color: '#999', fontSize: '11px' }}>
                  Detected: {anomaly.detected_at}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{
                  fontSize: '12px',
                  color: '#666',
                  marginBottom: '5px'
                }}>
                  Severity
                </div>
                <div style={{
                  fontSize: '16px',
                  fontWeight: 'bold',
                  color: getSeverityColor(anomaly.severity)
                }}>
                  {anomaly.severity}
                </div>
                <div style={{ fontSize: '10px', color: '#999', marginTop: '5px' }}>
                  Score: {(anomaly.score * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Selected Anomaly Details */}
        {selectedAnomaly && (
          <div style={{
            marginTop: '20px',
            padding: '15px',
            backgroundColor: '#fafafa',
            borderRadius: '8px',
            border: '1px solid #ddd'
          }}>
            <h4>Anomaly Analysis</h4>
            <div style={{ marginBottom: '10px' }}>
              <strong>Root Cause Hypotheses:</strong>
              <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                {selectedAnomaly.root_causes?.map((cause, idx) => (
                  <li key={idx} style={{ marginBottom: '5px', fontSize: '12px' }}>
                    {cause.factor}: {cause.correlation.toFixed(2)} correlation
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <strong>Recommended Actions:</strong>
              <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                {selectedAnomaly.recommended_actions?.map((action, idx) => (
                  <li key={idx} style={{ marginBottom: '5px', fontSize: '12px' }}>
                    {action}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    );
  };


  // ========================================================================
  // RENDER INSIGHTS
  // ========================================================================

  const renderInsights = () => {
    const unreadCount = insights.filter(i => !i.read).length;

    return (
      <div style={{ padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3>Smart Insights ({unreadCount} unread)</h3>
          <button
            onClick={generateInsights}
            disabled={loading}
            style={{
              padding: '10px 20px',
              backgroundColor: '#8884d8',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            {loading ? 'Generating...' : 'Generate Insights'}
          </button>
        </div>

        {insights.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
            No insights yet. Click "Generate Insights" to begin.
          </div>
        ) : (
          <div>
            {insights.map(insight => (
              <div
                key={insight.insight_id}
                onClick={() => markInsightAsRead(insight.insight_id)}
                style={{
                  backgroundColor: insight.read ? '#f5f5f5' : getSeverityBgColor(insight.severity),
                  border: `1px solid ${insight.read ? '#ddd' : getSeverityColor(insight.severity)}`,
                  borderRadius: '8px',
                  padding: '15px',
                  marginBottom: '10px',
                  cursor: 'pointer',
                  opacity: insight.read ? 0.7 : 1
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{
                      fontSize: '14px',
                      fontWeight: 'bold',
                      color: getSeverityColor(insight.severity),
                      marginBottom: '5px'
                    }}>
                      {insight.title}
                    </div>
                    <div style={{ color: '#666', fontSize: '13px', marginBottom: '8px' }}>
                      {insight.description}
                    </div>
                    <div style={{ fontSize: '11px', color: '#999' }}>
                      {insight.created_at}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
                      Relevance
                    </div>
                    <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#8884d8' }}>
                      {(insight.score * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };


  // ========================================================================
  // MAIN RENDER
  // ========================================================================

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h1>Predictive Insights Engine</h1>

      {/* Control Panel */}
      <div style={{
        marginBottom: '20px',
        padding: '15px',
        backgroundColor: '#f5f5f5',
        borderRadius: '8px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <label style={{ marginRight: '15px' }}>
            <strong>Metric:</strong>
            <select
              value={selectedMetric || ''}
              onChange={(e) => setSelectedMetric(e.target.value)}
              style={{ marginLeft: '10px', padding: '8px' }}
            >
              {metrics.map(m => (
                <option key={m.metric_id} value={m.metric_id}>
                  {m.name}
                </option>
              ))}
            </select>
          </label>
          
          <label style={{ marginRight: '15px' }}>
            <strong>Horizon:</strong>
            <input
              type="number"
              value={timeHorizon}
              onChange={(e) => setTimeHorizon(parseInt(e.target.value))}
              min="1"
              max="90"
              style={{ marginLeft: '10px', padding: '8px', width: '60px' }}
            />
            days
          </label>
        </div>

        {/* View Tabs */}
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => setViewMode('forecast')}
            style={{
              padding: '8px 16px',
              backgroundColor: viewMode === 'forecast' ? '#8884d8' : '#e0e0e0',
              color: viewMode === 'forecast' ? 'white' : '#666',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            📈 Forecast
          </button>
          <button
            onClick={() => setViewMode('anomalies')}
            style={{
              padding: '8px 16px',
              backgroundColor: viewMode === 'anomalies' ? '#d32f2f' : '#e0e0e0',
              color: viewMode === 'anomalies' ? 'white' : '#666',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            🚨 Anomalies ({anomalies.length})
          </button>
          <button
            onClick={() => setViewMode('insights')}
            style={{
              padding: '8px 16px',
              backgroundColor: viewMode === 'insights' ? '#4caf50' : '#e0e0e0',
              color: viewMode === 'insights' ? 'white' : '#666',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            💡 Insights ({insights.length})
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div style={{
        border: '1px solid #ddd',
        borderRadius: '8px',
        backgroundColor: 'white',
        minHeight: '500px'
      }}>
        {viewMode === 'forecast' && renderForecast()}
        {viewMode === 'anomalies' && renderAnomalies()}
        {viewMode === 'insights' && renderInsights()}
      </div>
    </div>
  );
};

export default PredictiveInsights;
