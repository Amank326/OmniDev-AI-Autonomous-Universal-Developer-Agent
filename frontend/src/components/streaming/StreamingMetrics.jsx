/**
 * Phase 24: Streaming Metrics Component
 * Live metrics display with real-time updates and trend visualization
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';

const StreamingMetrics = ({ metrics = {}, subscribeToMetric, unsubscribeFromMetric }) => {
  // Display state
  const [displayMetrics, setDisplayMetrics] = useState({});
  const [trends, setTrends] = useState({});
  const [trendHistory, setTrendHistory] = useState({});
  
  // Animation state
  const [animatingMetrics, setAnimatingMetrics] = useState(new Set());
  const metricRefsRef = useRef({});


  // ========================================================================
  // METRIC UPDATE HANDLING
  // ========================================================================

  useEffect(() => {
    setDisplayMetrics(metrics);
    
    // Trigger update animation
    Object.keys(metrics).forEach(metricId => {
      triggerUpdateAnimation(metricId);
    });
  }, [metrics]);

  const triggerUpdateAnimation = (metricId) => {
    setAnimatingMetrics(prev => new Set([...prev, metricId]));
    
    // Remove animation class after duration
    setTimeout(() => {
      setAnimatingMetrics(prev => {
        const next = new Set(prev);
        next.delete(metricId);
        return next;
      });
    }, 600); // 600ms animation duration
  };


  // ========================================================================
  // TREND DETECTION
  // ========================================================================

  const updateMetricTrend = useCallback((metricId, newValue, oldValue) => {
    if (!oldValue) return;
    
    const delta = newValue - oldValue;
    const changePercent = (delta / oldValue) * 100;
    
    let trend = 'stable';
    if (changePercent > 2) trend = 'increasing';
    else if (changePercent < -2) trend = 'decreasing';
    
    // Update trend history
    setTrendHistory(prev => ({
      ...prev,
      [metricId]: [...(prev[metricId] || []).slice(-59), { value: newValue, timestamp: Date.now() }],
    }));
    
    setTrends(prev => ({
      ...prev,
      [metricId]: trend,
    }));
  }, []);


  // ========================================================================
  // DATA QUALITY
  // ========================================================================

  const getDataQuality = (metricId) => {
    const history = trendHistory[metricId] || [];
    if (history.length === 0) return 'unknown';
    
    const recentUpdates = history.slice(-5);
    const timeDiffs = [];
    
    for (let i = 1; i < recentUpdates.length; i++) {
      timeDiffs.push(recentUpdates[i].timestamp - recentUpdates[i - 1].timestamp);
    }
    
    const avgTimeDiff = timeDiffs.reduce((a, b) => a + b, 0) / timeDiffs.length;
    
    if (avgTimeDiff < 5000) return 'excellent'; // < 5 seconds
    if (avgTimeDiff < 15000) return 'good'; // < 15 seconds
    if (avgTimeDiff < 60000) return 'fair'; // < 1 minute
    return 'poor'; // > 1 minute
  };


  // ========================================================================
  // FORMATTING
  // ========================================================================

  const formatNumber = (value, decimals = 2) => {
    if (typeof value !== 'number') return 'N/A';
    
    if (Math.abs(value) >= 1e6) {
      return (value / 1e6).toFixed(1) + 'M';
    }
    if (Math.abs(value) >= 1e3) {
      return (value / 1e3).toFixed(1) + 'K';
    }
    
    return value.toFixed(decimals);
  };

  const getThresholdStatus = (metricId, value) => {
    const metric = displayMetrics[metricId];
    if (!metric) return 'normal';
    
    if (metric.threshold_critical && value >= metric.threshold_critical) {
      return 'critical';
    }
    if (metric.threshold_warning && value >= metric.threshold_warning) {
      return 'warning';
    }
    
    return 'normal';
  };


  // ========================================================================
  // SPARKLINE RENDERING
  // ========================================================================

  const renderSparkline = (metricId, width = 100, height = 20) => {
    const history = trendHistory[metricId] || [];
    if (history.length < 2) return null;
    
    const values = history.map(h => h.value);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const range = maxValue - minValue || 1;
    
    const points = values.map((v, i) => {
      const x = (i / (values.length - 1)) * width;
      const y = height - ((v - minValue) / range) * height;
      return `${x},${y}`;
    }).join(' ');
    
    return (
      <svg width={width} height={height} style={{ display: 'inline-block' }}>
        <polyline
          points={points}
          fill="none"
          stroke="#8884d8"
          strokeWidth="1"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
    );
  };


  // ========================================================================
  // COMPONENT RENDERING
  // ========================================================================

  const getStatusColor = (status) => {
    switch (status) {
      case 'critical':
        return '#dc3545';
      case 'warning':
        return '#ffc107';
      case 'good':
        return '#28a745';
      default:
        return '#6c757d';
    }
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'increasing':
        return '📈';
      case 'decreasing':
        return '📉';
      default:
        return '→';
    }
  };

  const getQualityIcon = (quality) => {
    switch (quality) {
      case 'excellent':
        return '⭐⭐⭐';
      case 'good':
        return '⭐⭐';
      case 'fair':
        return '⭐';
      default:
        return '❓';
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h2>Live Metrics</h2>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
        gap: '15px',
      }}>
        {Object.entries(displayMetrics).map(([metricId, metric]) => {
          const isAnimating = animatingMetrics.has(metricId);
          const thresholdStatus = getThresholdStatus(metricId, metric.value);
          const quality = getDataQuality(metricId);
          const trend = trends[metricId] || 'stable';
          
          return (
            <div
              key={metricId}
              ref={(el) => (metricRefsRef.current[metricId] = el)}
              style={{
                border: `2px solid ${getStatusColor(thresholdStatus)}`,
                borderRadius: '8px',
                padding: '15px',
                backgroundColor: isAnimating ? '#f0f8ff' : 'white',
                transition: 'background-color 0.3s ease',
                boxShadow: isAnimating ? '0 0 10px rgba(136, 132, 216, 0.3)' : 'none',
              }}
            >
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <div>
                  <h3 style={{ margin: '0 0 5px 0' }}>{metric.name || metricId}</h3>
                  <span style={{ fontSize: '12px', color: '#666' }}>
                    {metric.unit || ''}
                  </span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontSize: '12px', color: '#666' }}>
                    {getQualityIcon(quality)}
                  </span>
                </div>
              </div>

              {/* Main Value Display */}
              <div style={{
                display: 'flex',
                alignItems: 'baseline',
                gap: '10px',
                marginBottom: '15px',
              }}>
                <div style={{
                  fontSize: '32px',
                  fontWeight: 'bold',
                  color: getStatusColor(thresholdStatus),
                }}>
                  {formatNumber(metric.value)}
                </div>
                <span style={{ fontSize: '20px' }}>
                  {getTrendIcon(trend)}
                </span>
              </div>

              {/* Delta & Change */}
              {metric.delta !== undefined && (
                <div style={{ marginBottom: '10px', fontSize: '14px', color: '#666' }}>
                  <div>
                    Change: <span style={{
                      color: metric.delta > 0 ? '#28a745' : metric.delta < 0 ? '#dc3545' : '#666',
                      fontWeight: 'bold',
                    }}>
                      {metric.delta > 0 ? '+' : ''}{formatNumber(metric.delta, 2)} ({metric.delta_percent}%)
                    </span>
                  </div>
                </div>
              )}

              {/* Thresholds */}
              {(metric.threshold_warning || metric.threshold_critical) && (
                <div style={{ marginBottom: '10px', fontSize: '12px', color: '#666' }}>
                  {metric.threshold_warning && (
                    <div>⚠️ Warning: {formatNumber(metric.threshold_warning)}</div>
                  )}
                  {metric.threshold_critical && (
                    <div>🔴 Critical: {formatNumber(metric.threshold_critical)}</div>
                  )}
                </div>
              )}

              {/* Sparkline */}
              <div style={{ marginBottom: '10px' }}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
                  Last 60 values:
                </div>
                {renderSparkline(metricId)}
              </div>

              {/* Statistics */}
              {trendHistory[metricId] && trendHistory[metricId].length > 0 && (
                <div style={{
                  fontSize: '12px',
                  color: '#999',
                  borderTop: '1px solid #eee',
                  paddingTop: '10px',
                }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <div>
                      Min: {formatNumber(Math.min(...trendHistory[metricId].map(h => h.value)))}
                    </div>
                    <div>
                      Max: {formatNumber(Math.max(...trendHistory[metricId].map(h => h.value)))}
                    </div>
                    <div>
                      Avg: {formatNumber(
                        trendHistory[metricId].reduce((a, h) => a + h.value, 0) / trendHistory[metricId].length
                      )}
                    </div>
                    <div>
                      Samples: {trendHistory[metricId].length}
                    </div>
                  </div>
                </div>
              )}

              {/* Last Updated */}
              <div style={{
                fontSize: '11px',
                color: '#aaa',
                marginTop: '10px',
                borderTop: '1px solid #eee',
                paddingTop: '8px',
              }}>
                Updated: {metric.updated_at ? new Date(metric.updated_at).toLocaleTimeString() : 'N/A'}
              </div>
            </div>
          );
        })}
      </div>

      {Object.keys(displayMetrics).length === 0 && (
        <div style={{
          textAlign: 'center',
          padding: '40px',
          color: '#999',
          backgroundColor: '#f5f5f5',
          borderRadius: '8px',
        }}>
          No metrics available. Subscribe to metrics to begin.
        </div>
      )}
    </div>
  );
};

export default StreamingMetrics;
