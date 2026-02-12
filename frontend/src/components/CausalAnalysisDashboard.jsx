import React, { useState, useCallback, useEffect } from 'react';
import {
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Treemap,
  Cell,
} from 'recharts';
import './CausalAnalysisDashboard.css';

const CausalAnalysisDashboard = ({ workspaceId, anomalyMetric, metrics }) => {
  const [analysis, setAnalysis] = useState(null);
  const [causalGraph, setCausalGraph] = useState(null);
  const [feedbackLoops, setFeedbackLoops] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState(null);
  const [viewMode, setViewMode] = useState('overview'); // overview, graph, loops, metrics
  const [expandedRootCause, setExpandedRootCause] = useState(null);
  const [socket, setSocket] = useState(null);

  // Connect WebSocket
  useEffect(() => {
    const newSocket = io(`http://localhost:5000/ml?workspace_id=${workspaceId}`);
    setSocket(newSocket);

    return () => {
      if (newSocket) newSocket.disconnect();
    };
  }, [workspaceId]);

  // Perform causal analysis
  const performCausalAnalysis = useCallback(async () => {
    if (!anomalyMetric || !metrics) return;

    setLoading(true);
    try {
      const response = await fetch(`http://localhost:5000/api/ml/causal/analyze?workspace_id=${workspaceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          anomaly_metric: anomalyMetric,
          anomaly_value: selectedMetric?.value || 100,
          baseline_value: selectedMetric?.baseline || 50,
          metrics,
        }),
      });

      const data = await response.json();
      setAnalysis(data);

      // Emit WebSocket event
      if (socket) {
        socket.emit('request_causal_analysis', {
          anomaly_metric: anomalyMetric,
          anomaly_value: selectedMetric?.value || 100,
          baseline_value: selectedMetric?.baseline || 50,
          metrics,
        });
      }
    } catch (error) {
      console.error('Causal analysis failed:', error);
    } finally {
      setLoading(false);
    }
  }, [anomalyMetric, metrics, selectedMetric, workspaceId, socket]);

  // Build causal graph
  const buildCausalGraph = useCallback(async () => {
    if (!metrics) return;

    try {
      const response = await fetch(`http://localhost:5000/api/ml/causal/graph?workspace_id=${workspaceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metrics }),
      });

      const data = await response.json();
      setCausalGraph(data);

      // Emit WebSocket event
      if (socket) {
        socket.emit('request_causal_graph', { metrics });
      }
    } catch (error) {
      console.error('Causal graph build failed:', error);
    }
  }, [metrics, workspaceId, socket]);

  // Detect feedback loops
  const detectFeedbackLoops = useCallback(async () => {
    if (!metrics) return;

    try {
      const response = await fetch(`http://localhost:5000/api/ml/causal/feedback-loops?workspace_id=${workspaceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metrics }),
      });

      const data = await response.json();
      setFeedbackLoops(data.feedback_loops || []);

      // Emit WebSocket event
      if (socket) {
        socket.emit('detect_feedback_loops', { metrics });
      }
    } catch (error) {
      console.error('Feedback loop detection failed:', error);
    }
  }, [metrics, workspaceId, socket]);

  // WebSocket listeners
  useEffect(() => {
    if (!socket) return;

    socket.on('causal_analysis_result', (data) => {
      setAnalysis(data);
    });

    socket.on('causal_graph_result', (data) => {
      setCausalGraph(data);
    });

    socket.on('feedback_loops_detected', (data) => {
      setFeedbackLoops(data.loops || []);
    });

    return () => {
      socket.off('causal_analysis_result');
      socket.off('causal_graph_result');
      socket.off('feedback_loops_detected');
    };
  }, [socket]);

  // Render overview
  const renderOverview = () => (
    <div className="analysis-overview">
      <div className="analysis-summary">
        <h3>Analysis Summary</h3>
        {analysis ? (
          <div className="summary-content">
            <div className="summary-item">
              <span className="label">Target Anomaly</span>
              <span className="value">{analysis.target_anomaly}</span>
            </div>
            <div className="summary-item">
              <span className="label">Confidence Score</span>
              <span className="value confidence">{(analysis.confidence_score * 100).toFixed(1)}%</span>
            </div>
            <div className="summary-item">
              <span className="label">Root Causes Identified</span>
              <span className="value">{analysis.root_causes?.length || 0}</span>
            </div>
            <p className="explanation">{analysis.explanation}</p>
          </div>
        ) : (
          <p className="no-data">No analysis performed yet</p>
        )}
      </div>

      <div className="root-causes-container">
        <h3>Root Causes Analysis</h3>
        {analysis?.root_causes && analysis.root_causes.length > 0 ? (
          <div className="root-causes-list">
            {analysis.root_causes.map((rc, idx) => (
              <div
                key={idx}
                className={`root-cause-item ${expandedRootCause === idx ? 'expanded' : ''}`}
                onClick={() => setExpandedRootCause(expandedRootCause === idx ? null : idx)}
              >
                <div className="rc-header">
                  <span className="metric-name">{rc.root_cause_metric}</span>
                  <div className="rc-stats">
                    <span className="contribution">{rc.contribution_percent.toFixed(1)}%</span>
                    <span className="confidence">{(rc.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
                {expandedRootCause === idx && (
                  <div className="rc-details">
                    <p className="description">{rc.description}</p>
                    <div className="recommended-actions">
                      <h4>Recommended Actions</h4>
                      <ul>
                        {rc.recommended_actions?.map((action, i) => (
                          <li key={i}>{action}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="no-data">No root causes identified</p>
        )}
      </div>

      <div className="insights-container">
        <h3>Actionable Insights</h3>
        {analysis?.actionable_insights && analysis.actionable_insights.length > 0 ? (
          <ul className="insights-list">
            {analysis.actionable_insights.map((insight, idx) => (
              <li key={idx} className="insight-item">{insight}</li>
            ))}
          </ul>
        ) : (
          <p className="no-data">No insights available</p>
        )}
      </div>
    </div>
  );

  // Render causal graph
  const renderGraph = () => (
    <div className="causal-graph-container">
      <h3>Causal Graph Visualization</h3>
      {causalGraph ? (
        <div className="graph-content">
          <div className="graph-stats">
            <div className="stat">
              <span className="label">Nodes (Metrics)</span>
              <span className="value">{causalGraph.total_nodes}</span>
            </div>
            <div className="stat">
              <span className="label">Relationships</span>
              <span className="value">{causalGraph.total_links}</span>
            </div>
          </div>

          {/* Node visualization */}
          <div className="graph-viz">
            <h4>Metrics Network</h4>
            <div className="node-list">
              {causalGraph.nodes?.slice(0, 10).map((node, idx) => (
                <div key={idx} className="node-item">
                  <span className="node-name">{node.label}</span>
                  <div className="node-info">
                    <span className="current">Now: {node.current_value.toFixed(1)}</span>
                    <span className="baseline">Base: {node.baseline_value.toFixed(1)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Link visualization */}
          <div className="links-viz">
            <h4>Causal Links</h4>
            <div className="links-list">
              {causalGraph.links?.slice(0, 8).map((link, idx) => (
                <div key={idx} className="link-item">
                  <span className="source">{link.source}</span>
                  <span className="arrow">→</span>
                  <span className="target">{link.target}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <p className="no-data">Build causal graph to visualize relationships</p>
      )}
    </div>
  );

  // Render feedback loops
  const renderLoops = () => (
    <div className="feedback-loops-container">
      <h3>Feedback Loops & Cycles</h3>
      {feedbackLoops && feedbackLoops.length > 0 ? (
        <div className="loops-content">
          <div className="loop-alert">
            <strong>⚠️ {feedbackLoops.length} feedback loop(s) detected</strong>
          </div>
          <div className="loops-list">
            {feedbackLoops.map((loop, idx) => (
              <div key={idx} className="loop-item">
                <div className="loop-sequence">
                  {loop.map((metric, i) => (
                    <React.Fragment key={i}>
                      <span className="metric">{metric}</span>
                      {i < loop.length - 1 && <span className="arrow">→</span>}
                    </React.Fragment>
                  ))}
                </div>
                <span className="loop-length">Length: {loop.length}</span>
              </div>
            ))}
          </div>
          <div className="loop-implications">
            <h4>Implications</h4>
            <ul>
              <li>Feedback loops can amplify anomalies</li>
              <li>Breaking loops may reduce issue propagation</li>
              <li>Consider circuit breakers or rate limiting</li>
            </ul>
          </div>
        </div>
      ) : (
        <p className="no-data">No feedback loops detected</p>
      )}
    </div>
  );

  // Render metrics
  const renderMetrics = () => (
    <div className="metrics-container">
      <h3>Correlation Metrics</h3>
      <div className="metrics-grid">
        {Object.entries(metrics || {}).slice(0, 6).map(([name, values]) => {
          if (!Array.isArray(values)) return null;
          const numValues = values.length;
          const current = values[values.length - 1];
          const baseline = values.reduce((a, b) => a + b, 0) / numValues;

          return (
            <div key={name} className="metric-card">
              <h4>{name.replace(/_/g, ' ')}</h4>
              <div className="metric-stat">
                <span className="current">{current?.toFixed(2) || 'N/A'}</span>
                <span className="baseline">Baseline: {baseline?.toFixed(2) || 'N/A'}</span>
              </div>
              <div className="mini-chart">
                <ResponsiveContainer width="100%" height={80}>
                  <LineChart data={values.slice(-5).map((v, i) => ({ index: i, value: v }))}>
                    <Line type="monotone" dataKey="value" stroke="#8884d8" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  return (
    <div className="causal-analysis-dashboard">
      <div className="dashboard-header">
        <h2>Causal Analysis Dashboard</h2>
        <div className="header-controls">
          <button
            className="btn btn-primary"
            onClick={performCausalAnalysis}
            disabled={loading || !anomalyMetric}
          >
            {loading ? 'Analyzing...' : 'Analyze Causality'}
          </button>
          <button className="btn btn-secondary" onClick={buildCausalGraph}>
            Build Graph
          </button>
          <button className="btn btn-secondary" onClick={detectFeedbackLoops}>
            Detect Loops
          </button>
        </div>
      </div>

      <div className="view-tabs">
        <button
          className={`tab ${viewMode === 'overview' ? 'active' : ''}`}
          onClick={() => setViewMode('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${viewMode === 'graph' ? 'active' : ''}`}
          onClick={() => setViewMode('graph')}
        >
          Causal Graph
        </button>
        <button
          className={`tab ${viewMode === 'loops' ? 'active' : ''}`}
          onClick={() => setViewMode('loops')}
        >
          Feedback Loops
        </button>
        <button
          className={`tab ${viewMode === 'metrics' ? 'active' : ''}`}
          onClick={() => setViewMode('metrics')}
        >
          Metrics
        </button>
      </div>

      <div className="dashboard-content">
        {viewMode === 'overview' && renderOverview()}
        {viewMode === 'graph' && renderGraph()}
        {viewMode === 'loops' && renderLoops()}
        {viewMode === 'metrics' && renderMetrics()}
      </div>
    </div>
  );
};

export default CausalAnalysisDashboard;
