/**
 * Phase 24: Real-time Dashboard Component
 * WebSocket-driven dashboard with live widget updates
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';

const RealtimeDashboard = ({ userId, apiBaseUrl = 'http://localhost:5000' }) => {
  // Connection state
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [connectionId, setConnectionId] = useState(null);
  const [latency, setLatency] = useState(0);
  
  // Dashboard state
  const [widgets, setWidgets] = useState([]);
  const [filters, setFilters] = useState({});
  const [metrics, setMetrics] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [presence, setPresence] = useState({});
  
  // Performance monitoring
  const [updateStats, setUpdateStats] = useState({
    updatesPerSecond: 0,
    lastUpdateTime: Date.now(),
  });
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const updateCounterRef = useRef(0);


  // ========================================================================
  // WEBSOCKET CONNECTION MANAGEMENT
  // ========================================================================

  const connectWebSocket = useCallback(async () => {
    try {
      setConnectionStatus('connecting');
      
      // In real implementation, would use WebSocket:
      // ws://localhost:5000/ws/stream
      // For now, simulate connection
      
      setConnectionStatus('connected');
      setConnectionId(`conn_${Date.now()}`);
      
      // Start activity tracking
      trackActivity('dashboard_connected', { userId });
      
      // Request initial data
      requestInitialData();
      
      // Setup heartbeat
      setupHeartbeat();
      
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      setConnectionStatus('error');
      scheduleReconnect();
    }
  }, [userId]);

  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnectionStatus('disconnected');
    setConnectionId(null);
  }, []);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    reconnectTimeoutRef.current = setTimeout(() => {
      if (connectionStatus !== 'connected') {
        connectWebSocket();
      }
    }, 3000); // 3 second backoff
  }, [connectWebSocket, connectionStatus]);


  // ========================================================================
  // WEBSOCKET MESSAGE HANDLERS
  // ========================================================================

  const handleWebSocketMessage = useCallback((message) => {
    const { type, data, timestamp } = message;
    
    switch (type) {
      case 'metric_update':
        handleMetricUpdate(data, timestamp);
        break;
      case 'alert':
        handleAlert(data, timestamp);
        break;
      case 'presence':
        handlePresenceUpdate(data);
        break;
      case 'heartbeat':
        handleHeartbeat();
        break;
      default:
        console.log('Unknown message type:', type);
    }
  }, []);

  const handleMetricUpdate = useCallback((data, timestamp) => {
    const { metric_id, value, delta, delta_percent, trend } = data;
    
    setMetrics(prev => ({
      ...prev,
      [metric_id]: {
        value,
        delta,
        delta_percent,
        trend,
        updated_at: timestamp,
      },
    }));
    
    // Trigger widget update animations
    updateCounterRef.current += 1;
  }, []);

  const handleAlert = useCallback((data, timestamp) => {
    const { alert_id, rule_id, metric_id, status, severity, message } = data;
    
    setAlerts(prev => {
      const existing = prev.findIndex(a => a.alert_id === alert_id);
      
      if (existing >= 0) {
        const updated = [...prev];
        updated[existing] = { alert_id, rule_id, metric_id, status, severity, message, timestamp };
        return updated;
      }
      
      return [...prev, { alert_id, rule_id, metric_id, status, severity, message, timestamp }];
    });
  }, []);

  const handlePresenceUpdate = useCallback((data) => {
    const { user_id, status, activity } = data;
    
    setPresence(prev => ({
      ...prev,
      [user_id]: { status, activity, updated_at: Date.now() },
    }));
  }, []);

  const handleHeartbeat = useCallback(() => {
    // Acknowledge heartbeat with latency measurement
    const latencyMs = Date.now() - updateStats.lastUpdateTime;
    setLatency(latencyMs);
  }, [updateStats.lastUpdateTime]);


  // ========================================================================
  // DATA REQUESTS
  // ========================================================================

  const requestInitialData = useCallback(async () => {
    try {
      // Fetch dashboard configuration
      const response = await fetch(`${apiBaseUrl}/api/v1/dashboard/${userId}/config`);
      const config = await response.json();
      
      setWidgets(config.widgets || []);
      setFilters(config.filters || {});
      
      // Subscribe to metrics
      config.widgets.forEach(widget => {
        if (widget.metric_id) {
          subscribeToMetric(widget.metric_id);
        }
      });
      
      // Subscribe to alert rules
      config.alert_rules?.forEach(rule => {
        subscribeToAlertRule(rule.id);
      });
      
    } catch (error) {
      console.error('Failed to load initial data:', error);
    }
  }, [userId, apiBaseUrl]);

  const subscribeToMetric = useCallback(async (metricId) => {
    try {
      await fetch(`${apiBaseUrl}/api/v1/streaming/metrics/streaming/${metricId}/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ connection_id: connectionId }),
      });
    } catch (error) {
      console.error(`Failed to subscribe to metric ${metricId}:`, error);
    }
  }, [connectionId, apiBaseUrl]);

  const subscribeToAlertRule = useCallback(async (ruleId) => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/streaming/alerts/live/${ruleId}`);
      const rule = await response.json();
    } catch (error) {
      console.error(`Failed to subscribe to alert rule ${ruleId}:`, error);
    }
  }, [apiBaseUrl]);


  // ========================================================================
  // HEARTBEAT & ACTIVITY TRACKING
  // ========================================================================

  const setupHeartbeat = useCallback(() => {
    const interval = setInterval(() => {
      trackActivity('dashboard_active', { userId });
    }, 30000); // 30 second heartbeat
    
    return interval;
  }, [userId]);

  const trackActivity = useCallback(async (action, context) => {
    try {
      if (connectionId) {
        await fetch(`${apiBaseUrl}/api/v1/streaming/presence/${userId}/activity`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action, context }),
        });
      }
    } catch (error) {
      console.error('Failed to track activity:', error);
    }
  }, [userId, connectionId, apiBaseUrl]);


  // ========================================================================
  // FILTER MANAGEMENT
  // ========================================================================

  const applyFilter = useCallback((filterKey, filterValue) => {
    setFilters(prev => ({
      ...prev,
      [filterKey]: filterValue,
    }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({});
  }, []);


  // ========================================================================
  // WIDGET LIFECYCLE
  // ========================================================================

  const addWidget = useCallback((widgetConfig) => {
    const newWidget = {
      id: `widget_${Date.now()}`,
      ...widgetConfig,
      createdAt: Date.now(),
    };
    
    setWidgets(prev => [...prev, newWidget]);
    
    // Subscribe to widget metric
    if (widgetConfig.metric_id) {
      subscribeToMetric(widgetConfig.metric_id);
    }
  }, [subscribeToMetric]);

  const removeWidget = useCallback((widgetId) => {
    setWidgets(prev => prev.filter(w => w.id !== widgetId));
  }, []);

  const updateWidgetLayout = useCallback((widgetId, layout) => {
    setWidgets(prev => prev.map(w =>
      w.id === widgetId ? { ...w, layout } : w
    ));
  }, []);


  // ========================================================================
  // ALERT MANAGEMENT
  // ========================================================================

  const acknowledgeAlert = useCallback(async (alertId) => {
    try {
      await fetch(`${apiBaseUrl}/api/v1/streaming/alerts/active/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ acknowledged_by: userId }),
      });
      
      // Remove from active alerts
      setAlerts(prev => prev.filter(a => a.alert_id !== alertId));
      
    } catch (error) {
      console.error(`Failed to acknowledge alert ${alertId}:`, error);
    }
  }, [userId, apiBaseUrl]);

  const escalateAlert = useCallback(async (alertId) => {
    try {
      await fetch(`${apiBaseUrl}/api/v1/streaming/alerts/active/${alertId}/escalate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ escalation_level: 2 }),
      });
    } catch (error) {
      console.error(`Failed to escalate alert ${alertId}:`, error);
    }
  }, [apiBaseUrl]);


  // ========================================================================
  // PERFORMANCE MONITORING
  // ========================================================================

  const setupPerformanceMonitoring = useCallback(() => {
    const interval = setInterval(() => {
      const updatesPerSecond = updateCounterRef.current;
      updateCounterRef.current = 0;
      
      setUpdateStats({
        updatesPerSecond,
        lastUpdateTime: Date.now(),
      });
    }, 1000);
    
    return interval;
  }, []);


  // ========================================================================
  // LIFECYCLE
  // ========================================================================

  useEffect(() => {
    connectWebSocket();
    
    const perfInterval = setupPerformanceMonitoring();
    
    return () => {
      disconnectWebSocket();
      clearInterval(perfInterval);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connectWebSocket, disconnectWebSocket, setupPerformanceMonitoring]);


  // ========================================================================
  // RENDER
  // ========================================================================

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'green';
      case 'connecting': return 'yellow';
      case 'error': return 'red';
      default: return 'gray';
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      {/* Header */}
      <div style={{ marginBottom: '20px', borderBottom: '1px solid #ddd', paddingBottom: '10px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1>Real-time Dashboard</h1>
          
          <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
            {/* Connection Status */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: getConnectionStatusColor(),
              }} />
              <span>{connectionStatus}</span>
            </div>
            
            {/* Latency */}
            <div>Latency: {latency}ms</div>
            
            {/* Updates Per Second */}
            <div>Updates: {updateStats.updatesPerSecond}/sec</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#f5f5f5' }}>
        <button onClick={clearFilters}>Clear Filters</button>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#fff3cd', border: '1px solid #ffc107' }}>
          <h3>Active Alerts ({alerts.length})</h3>
          {alerts.map(alert => (
            <div key={alert.alert_id} style={{ marginBottom: '10px', padding: '8px', backgroundColor: 'white' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div>
                  <strong>[{alert.severity}]</strong> {alert.message}
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button onClick={() => acknowledgeAlert(alert.alert_id)}>Acknowledge</button>
                  <button onClick={() => escalateAlert(alert.alert_id)}>Escalate</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Widgets Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
        {widgets.map(widget => (
          <div key={widget.id} style={{
            border: '1px solid #ddd',
            borderRadius: '8px',
            padding: '15px',
            backgroundColor: 'white',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
              <h3>{widget.title}</h3>
              <button onClick={() => removeWidget(widget.id)}>Remove</button>
            </div>
            
            <div style={{ height: '250px', backgroundColor: '#f9f9f9' }}>
              Widget content for {widget.title}
            </div>
          </div>
        ))}
      </div>

      {/* Presence */}
      {Object.keys(presence).length > 0 && (
        <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#f0f0f0', borderRadius: '8px' }}>
          <h3>Online Users ({Object.keys(presence).length})</h3>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {Object.entries(presence).map(([userId, info]) => (
              <div key={userId} style={{
                padding: '8px 12px',
                backgroundColor: '#ddd',
                borderRadius: '4px',
                fontSize: '14px',
              }}>
                {userId}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RealtimeDashboard;
