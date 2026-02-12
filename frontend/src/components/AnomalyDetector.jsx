import React, { useState, useEffect } from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart } from 'recharts';
import './AnomalyDetector.css';

const AnomalyDetector = ({ workspaceId, refreshInterval = 5000 }) => {
  const [anomalies, setAnomalies] = useState([]);
  const [patterns, setPatterns] = useState([]);
  const [rootCauses, setRootCauses] = useState({});
  const [remediations, setRemediations] = useState([]);
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('timeline');
  const [detectionSensitivity, setDetectionSensitivity] = useState('medium');

  // Fetch anomalies
  useEffect(() => {
    const fetchAnomalies = async () => {
      try {
        const response = await fetch(
          '/api/v1/ml_advanced/anomalies/history?lookback_days=30',
          {
            headers: { 'X-Workspace-ID': workspaceId },
          }
        );
        const data = await response.json();
        if (data.success) {
          setAnomalies(data.anomalies);
          if (data.anomalies.length > 0 && !selectedAnomaly) {
            setSelectedAnomaly(data.anomalies[0]);
          }
          setLoading(false);
        }
      } catch (error) {
        console.error('Failed to fetch anomalies:', error);
        setLoading(false);
      }
    };

    fetchAnomalies();
    const interval = setInterval(fetchAnomalies, refreshInterval);
    return () => clearInterval(interval);
  }, [workspaceId, refreshInterval, selectedAnomaly]);

  // Fetch patterns
  useEffect(() => {
    const fetchPatterns = async () => {
      try {
        const response = await fetch(
          '/api/v1/ml_advanced/anomalies/patterns?lookback_days=90',
          {
            headers: { 'X-Workspace-ID': workspaceId },
          }
        );
        const data = await response.json();
        if (data.success) {
          setPatterns(data.patterns);
        }
      } catch (error) {
        console.error('Failed to fetch patterns:', error);
      }
    };

    fetchPatterns();
    const interval = setInterval(fetchPatterns, refreshInterval * 2);
    return () => clearInterval(interval);
  }, [workspaceId, refreshInterval]);

  // Analyze root cause when anomaly is selected
  useEffect(() => {
    if (!selectedAnomaly || rootCauses[selectedAnomaly.anomaly_id]) return;

    const analyzeRootCause = async () => {
      try {
        const response = await fetch('/api/v1/ml_advanced/anomalies/root-cause', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Workspace-ID': workspaceId,
          },
          body: JSON.stringify({
            anomaly_id: selectedAnomaly.anomaly_id,
            anomaly: selectedAnomaly,
          }),
        });
        const data = await response.json();
        if (data.success) {
          setRootCauses((prev) => ({
            ...prev,
            [selectedAnomaly.anomaly_id]: data.analysis,
          }));

          // Generate remediation plan
          const remResponse = await fetch('/api/v1/ml_advanced/automation/generate-remediation', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Workspace-ID': workspaceId,
            },
            body: JSON.stringify({
              anomaly: selectedAnomaly,
              root_cause: data.analysis,
            }),
          });
          const remData = await remResponse.json();
          if (remData.success) {
            setRemediations(remData.remediations);
          }
        }
      } catch (error) {
        console.error('Failed to analyze root cause:', error);
      }
    };

    analyzeRootCause();
  }, [selectedAnomaly, workspaceId, rootCauses]);

  // Severity color mapping
  const getSeverityColor = (severity) => {
    const colors = {
      critical: '#ef4444',
      high: '#f97316',
      medium: '#eab308',
      low: '#22c55e',
      info: '#3b82f6',
    };
    return colors[severity] || '#6b7280';
  };

  // Timeline View
  const TimelineView = () => (
    <div className="timeline-view">
      <h2>Anomaly Timeline</h2>
      <div className="timeline-container">
        <div className="timeline-list">
          {anomalies.map((anomaly, idx) => (
            <div
              key={idx}
              className={`timeline-item ${anomaly.severity} ${selectedAnomaly?.anomaly_id === anomaly.anomaly_id ? 'selected' : ''}`}
              onClick={() => setSelectedAnomaly(anomaly)}
              style={{ borderLeftColor: getSeverityColor(anomaly.severity) }}
            >
              <div className="timeline-header">
                <span className="metric-name">{anomaly.metrics[0]}</span>
                <span className="severity-badge" style={{ backgroundColor: getSeverityColor(anomaly.severity) }}>
                  {anomaly.severity.toUpperCase()}
                </span>
              </div>
              <div className="timeline-details">
                <p>Impact Score: <strong>{anomaly.impact_score}</strong></p>
                <time>{new Date(anomaly.detected_at).toLocaleString()}</time>
              </div>
              <div className="timeline-expand">→</div>
            </div>
          ))}
        </div>

        {selectedAnomaly && (
          <div className="timeline-detail-panel">
            <h3>Anomaly Details</h3>
            <div className="detail-content">
              <div className="detail-row">
                <span className="label">ID:</span>
                <span className="value">{selectedAnomaly.anomaly_id}</span>
              </div>
              <div className="detail-row">
                <span className="label">Metrics Affected:</span>
                <span className="value">{selectedAnomaly.metrics.join(', ')}</span>
              </div>
              <div className="detail-row">
                <span className="label">Severity:</span>
                <span className="value" style={{ color: getSeverityColor(selectedAnomaly.severity) }}>
                  {selectedAnomaly.severity.toUpperCase()}
                </span>
              </div>
              <div className="detail-row">
                <span className="label">Impact Score:</span>
                <span className="value">{selectedAnomaly.impact_score}%</span>
              </div>
              <div className="detail-row">
                <span className="label">Detected At:</span>
                <span className="value">{new Date(selectedAnomaly.detected_at).toLocaleString()}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  // Root Cause Analysis View
  const RootCauseView = () => {
    const rca = selectedAnomaly ? rootCauses[selectedAnomaly.anomaly_id] : null;

    return (
      <div className="root-cause-view">
        <h2>Root Cause Analysis</h2>
        {rca ? (
          <div className="rca-content">
            <div className="rca-summary">
              <div className="primary-cause">
                <h3>Primary Root Cause</h3>
                <div className="cause-card">
                  <span className="cause-type">{rca.primary_root_cause}</span>
                  <div className="confidence">
                    Confidence: <strong>{(rca.confidence * 100).toFixed(1)}%</strong>
                  </div>
                </div>
              </div>

              <div className="all-causes">
                <h3>All Identified Causes</h3>
                {rca.root_causes.map((cause, idx) => (
                  <div key={idx} className="cause-item">
                    <div className="cause-header">
                      <span className="type">{cause.type}</span>
                      <span className="confidence">{(cause.confidence_score * 100).toFixed(1)}%</span>
                    </div>
                    <p className="description">{cause.description}</p>
                  </div>
                ))}
              </div>

              <div className="evidence-section">
                <h3>Evidence</h3>
                <ul>
                  {rca.evidence.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ) : (
          <div className="empty-state">
            Select an anomaly to view root cause analysis
          </div>
        )}
      </div>
    );
  };

  // Remediation View
  const RemediationView = () => (
    <div className="remediation-view">
      <h2>Remediation Actions</h2>
      {remediations.length > 0 ? (
        <div className="remediation-list">
          {remediations.map((rem, idx) => (
            <div key={idx} className="remediation-card">
              <div className="remediation-header">
                <h3>{rem.action_type}</h3>
                <span className={`risk-badge ${rem.risk_level}`}>
                  {rem.risk_level.toUpperCase()}
                </span>
                {rem.automatic && <span className="auto-badge">AUTO</span>}
              </div>
              <p className="description">{rem.description}</p>
              <div className="remediation-details">
                <div className="detail">
                  <span className="label">Estimated Time:</span>
                  <span className="value">{rem.estimated_time_minutes} min</span>
                </div>
                <div className="detail">
                  <span className="label">Automatic:</span>
                  <span className="value">{rem.automatic ? 'Yes' : 'No'}</span>
                </div>
              </div>
              <div className="steps">
                <span className="steps-label">Steps:</span>
                <ol>
                  {rem.steps.map((step, sidx) => (
                    <li key={sidx}>{step}</li>
                  ))}
                </ol>
              </div>
              <div className="rollback">
                <strong>Rollback Plan:</strong>
                <p>{rem.rollback}</p>
              </div>
              <button className="execute-btn">Execute Remediation</button>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          No remediations available. Select an anomaly to generate a remediation plan.
        </div>
      )}
    </div>
  );

  // Patterns View
  const PatternsView = () => (
    <div className="patterns-view">
      <h2>Recurring Anomaly Patterns</h2>
      <div className="patterns-grid">
        {patterns.map((pattern, idx) => (
          <div key={idx} className="pattern-card">
            <h3>{pattern.pattern_name}</h3>
            <div className="pattern-details">
              <div className="detail">
                <span className="label">Metrics:</span>
                <span className="value">{pattern.metrics.join(', ')}</span>
              </div>
              <div className="detail">
                <span className="label">Frequency:</span>
                <span className="value">{pattern.frequency}</span>
              </div>
              <div className="detail">
                <span className="label">Occurrences:</span>
                <span className="value">{pattern.occurrences}</span>
              </div>
              <div className="detail">
                <span className="label">Avg Duration:</span>
                <span className="value">{pattern.average_duration_hours.toFixed(1)}h</span>
              </div>
              <div className="detail">
                <span className="label">Seasonal:</span>
                <span className="value">{pattern.seasonal ? 'Yes' : 'No'}</span>
              </div>
            </div>
            <div className="recommendation">
              <strong>Recommendation:</strong>
              <p>{pattern.recommendation}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  if (loading) {
    return <div className="loading">Loading Anomaly Detector...</div>;
  }

  return (
    <div className="anomaly-detector">
      <div className="header">
        <h1>Anomaly Detection & Root Cause Analysis</h1>
        <div className="sensitivity-control">
          <label htmlFor="sensitivity">Detection Sensitivity:</label>
          <select
            id="sensitivity"
            value={detectionSensitivity}
            onChange={(e) => setDetectionSensitivity(e.target.value)}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
      </div>

      {/* Statistics */}
      <div className="stats-bar">
        <div className="stat">
          <span className="stat-label">Total Anomalies</span>
          <span className="stat-value">{anomalies.length}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Critical</span>
          <span className="stat-value critical">{anomalies.filter((a) => a.severity === 'critical').length}</span>
        </div>
        <div className="stat">
          <span className="stat-label">High</span>
          <span className="stat-value high">{anomalies.filter((a) => a.severity === 'high').length}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Medium</span>
          <span className="stat-value medium">{anomalies.filter((a) => a.severity === 'medium').length}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Patterns Found</span>
          <span className="stat-value">{patterns.length}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'timeline' ? 'active' : ''}`}
          onClick={() => setActiveTab('timeline')}
        >
          Timeline
        </button>
        <button
          className={`tab ${activeTab === 'root-cause' ? 'active' : ''}`}
          onClick={() => setActiveTab('root-cause')}
        >
          Root Cause
        </button>
        <button
          className={`tab ${activeTab === 'remediation' ? 'active' : ''}`}
          onClick={() => setActiveTab('remediation')}
        >
          Remediation
        </button>
        <button
          className={`tab ${activeTab === 'patterns' ? 'active' : ''}`}
          onClick={() => setActiveTab('patterns')}
        >
          Patterns
        </button>
      </div>

      {/* Content */}
      <div className="tab-content">
        {activeTab === 'timeline' && <TimelineView />}
        {activeTab === 'root-cause' && <RootCauseView />}
        {activeTab === 'remediation' && <RemediationView />}
        {activeTab === 'patterns' && <PatternsView />}
      </div>
    </div>
  );
};

export default AnomalyDetector;
