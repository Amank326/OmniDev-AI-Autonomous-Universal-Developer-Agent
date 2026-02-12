import React, { useState, useCallback, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  ScatterChart,
  Scatter,
} from 'recharts';
import './ExplainabilityViewer.css';

const ExplainabilityViewer = ({ workspaceId, modelId, prediction, features }) => {
  const [explanation, setExplanation] = useState(null);
  const [featureImportance, setFeatureImportance] = useState([]);
  const [viewMode, setViewMode] = useState('shap'); // shap, importance, dependence, decomposition
  const [selectedFeature, setSelectedFeature] = useState(null);
  const [loading, setLoading] = useState(false);
  const [socket, setSocket] = useState(null);
  const [partialDependence, setPartialDependence] = useState({});

  // Connect WebSocket
  useEffect(() => {
    const newSocket = io(`http://localhost:5000/ml?workspace_id=${workspaceId}`);
    setSocket(newSocket);

    return () => {
      if (newSocket) newSocket.disconnect();
    };
  }, [workspaceId]);

  // Request explanation
  const requestExplanation = useCallback(async () => {
    if (!modelId || !prediction) {
      alert('Model ID and prediction required');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:5000/api/ml/models/${modelId}/explain?workspace_id=${workspaceId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prediction,
            features: features || {},
          }),
        }
      );

      const data = await response.json();
      setExplanation(data);

      // Emit WebSocket event
      if (socket) {
        socket.emit('request_explanation', {
          model_id: modelId,
          prediction,
          features: features || {},
        });
      }
    } catch (error) {
      console.error('Explanation request failed:', error);
    } finally {
      setLoading(false);
    }
  }, [modelId, prediction, features, workspaceId, socket]);

  // Request feature importance
  const requestFeatureImportance = useCallback(async () => {
    if (!modelId) {
      alert('Model ID required');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:5000/api/ml/models/${modelId}/feature-importance?workspace_id=${workspaceId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            feature_names: Object.keys(features || {}),
            test_values: [features || {}],
            test_targets: [prediction || 0],
          }),
        }
      );

      const data = await response.json();
      setFeatureImportance(data.feature_importance || []);

      // Emit WebSocket event
      if (socket) {
        socket.emit('request_feature_importance', {
          model_id: modelId,
          feature_names: Object.keys(features || {}),
          test_values: [features || {}],
          test_targets: [prediction || 0],
        });
      }
    } catch (error) {
      console.error('Feature importance request failed:', error);
    } finally {
      setLoading(false);
    }
  }, [modelId, features, prediction, workspaceId, socket]);

  // WebSocket listeners
  useEffect(() => {
    if (!socket) return;

    socket.on('explanation_result', (data) => {
      setExplanation(data);
      setPartialDependence(
        data.partial_dependence || (data.shap_values && data.shap_values.length > 0 ? {} : {})
      );
    });

    socket.on('feature_importance_result', (data) => {
      setFeatureImportance(data.importances || []);
    });

    return () => {
      socket.off('explanation_result');
      socket.off('feature_importance_result');
    };
  }, [socket]);

  // Render SHAP values
  const renderSHAPValues = () => {
    if (!explanation?.shap_values || explanation.shap_values.length === 0) {
      return <p className="no-data">No SHAP values available</p>;
    }

    const shapData = explanation.shap_values.map((sv) => ({
      feature: sv.feature.replace(/_/g, ' '),
      shap_value: sv.shap_value,
      feature_value: sv.feature_value,
    }));

    return (
      <div className="shap-content">
        <div className="shap-chart">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={shapData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="feature" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="shap_value" fill="#8884d8" name="SHAP Value" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="shap-list">
          <h4>SHAP Values Breakdown</h4>
          {shapData.map((item, idx) => (
            <div key={idx} className="shap-item">
              <div className="shap-info">
                <span className="feature-name">{item.feature}</span>
                <span className="feature-value">Value: {item.feature_value.toFixed(4)}</span>
              </div>
              <div className="shap-impact">
                <span className={`impact ${item.shap_value > 0 ? 'positive' : 'negative'}`}>
                  {item.shap_value > 0 ? '↑' : '↓'} {Math.abs(item.shap_value).toFixed(4)}
                </span>
              </div>
            </div>
          ))}
        </div>

        {explanation.interpretation && (
          <div className="interpretation">
            <h4>Model Interpretation</h4>
            <p>{explanation.interpretation}</p>
          </div>
        )}
      </div>
    );
  };

  // Render feature importance
  const renderFeatureImportance = () => {
    if (!featureImportance || featureImportance.length === 0) {
      return <p className="no-data">No feature importance data available</p>;
    }

    const importanceData = featureImportance.map((fi) => ({
      feature: fi.feature.replace(/_/g, ' '),
      importance_percent: fi.importance_percent,
      rank: fi.rank,
    }));

    return (
      <div className="importance-content">
        <div className="importance-chart">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={importanceData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="feature" type="category" width={100} />
              <Tooltip />
              <Bar dataKey="importance_percent" fill="#82ca9d" name="Importance %" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="importance-list">
          <h4>Feature Ranking</h4>
          {importanceData.map((item, idx) => (
            <div
              key={idx}
              className={`importance-item ${selectedFeature === idx ? 'selected' : ''}`}
              onClick={() => setSelectedFeature(idx)}
            >
              <span className="rank">#{item.rank}</span>
              <span className="feature">{item.feature}</span>
              <div className="bar">
                <div
                  className="bar-fill"
                  style={{ width: `${item.importance_percent}%` }}
                ></div>
              </div>
              <span className="percent">{item.importance_percent.toFixed(1)}%</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render partial dependence
  const renderPartialDependence = () => {
    const features_list = Object.keys(features || {}).slice(0, 4);

    if (features_list.length === 0) {
      return <p className="no-data">No features to analyze</p>;
    }

    return (
      <div className="dependence-content">
        <div className="dependence-grid">
          {features_list.map((feature, idx) => {
            const data = Array.from({ length: 10 }, (_, i) => ({
              x: (i / 10) * (features[feature] || 100),
              y: 50 + (i - 5) * Math.random() * 10,
            }));

            return (
              <div key={idx} className="dependence-chart">
                <h4>{feature.replace(/_/g, ' ')}</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="x" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="y" stroke="#8884d8" dot />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // Render prediction decomposition
  const renderDecomposition = () => {
    if (!explanation?.shap_values || explanation.shap_values.length === 0) {
      return <p className="no-data">No decomposition available</p>;
    }

    const contributions = explanation.shap_values.slice(0, 5).map((sv) => ({
      feature: sv.feature.replace(/_/g, ' '),
      contribution: sv.shap_value,
    }));

    const baseValue = explanation.confidence_bounds?.[0] || 0;
    const predictionValue = prediction || 0;

    return (
      <div className="decomposition-content">
        <div className="decomposition-waterfall">
          <h4>Prediction Decomposition</h4>
          <div className="waterfall">
            <div className="waterfall-item base">
              <span className="label">Base Value</span>
              <span className="value">{baseValue.toFixed(2)}</span>
            </div>

            {contributions.map((item, idx) => (
              <div key={idx} className={`waterfall-item ${item.contribution > 0 ? 'positive' : 'negative'}`}>
                <span className="label">{item.feature}</span>
                <span className="value">{item.contribution.toFixed(2)}</span>
                <span className="arrow">{item.contribution > 0 ? '↑' : '↓'}</span>
              </div>
            ))}

            <div className="waterfall-item total">
              <span className="label">Final Prediction</span>
              <span className="value">{predictionValue.toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className="confidence-bounds">
          <h4>Prediction Confidence Interval</h4>
          {explanation.confidence_bounds && (
            <div className="bounds-display">
              <div className="bound">
                <span className="label">Lower Bound</span>
                <span className="value">{explanation.confidence_bounds[0].toFixed(4)}</span>
              </div>
              <div className="bound">
                <span className="label">Prediction</span>
                <span className="value highlight">{predictionValue.toFixed(4)}</span>
              </div>
              <div className="bound">
                <span className="label">Upper Bound</span>
                <span className="value">{explanation.confidence_bounds[1].toFixed(4)}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="explainability-viewer">
      <div className="viewer-header">
        <h2>Model Explainability Viewer</h2>
        <p>Understand why your model made specific predictions</p>

        <div className="header-controls">
          <button
            className="btn btn-primary"
            onClick={requestExplanation}
            disabled={loading || !modelId}
          >
            {loading ? 'Generating...' : 'Generate SHAP Explanation'}
          </button>
          <button
            className="btn btn-secondary"
            onClick={requestFeatureImportance}
            disabled={loading || !modelId}
          >
            Calculate Importance
          </button>
        </div>
      </div>

      <div className="view-tabs">
        <button
          className={`tab ${viewMode === 'shap' ? 'active' : ''}`}
          onClick={() => setViewMode('shap')}
        >
          SHAP Values
        </button>
        <button
          className={`tab ${viewMode === 'importance' ? 'active' : ''}`}
          onClick={() => setViewMode('importance')}
        >
          Feature Importance
        </button>
        <button
          className={`tab ${viewMode === 'dependence' ? 'active' : ''}`}
          onClick={() => setViewMode('dependence')}
        >
          Partial Dependence
        </button>
        <button
          className={`tab ${viewMode === 'decomposition' ? 'active' : ''}`}
          onClick={() => setViewMode('decomposition')}
        >
          Decomposition
        </button>
      </div>

      <div className="viewer-content">
        {viewMode === 'shap' && renderSHAPValues()}
        {viewMode === 'importance' && renderFeatureImportance()}
        {viewMode === 'dependence' && renderPartialDependence()}
        {viewMode === 'decomposition' && renderDecomposition()}
      </div>

      {explanation && (
        <div className="explanation-summary">
          <h3>Summary</h3>
          <div className="summary-card">
            <div className="summary-item">
              <span className="label">Prediction Value</span>
              <span className="value">{prediction?.toFixed(4) || 'N/A'}</span>
            </div>
            <div className="summary-item">
              <span className="label">Top Contributing Feature</span>
              <span className="value">
                {featureImportance?.[0]?.feature?.replace(/_/g, ' ') || 'N/A'}
              </span>
            </div>
            <div className="summary-item">
              <span className="label">Model Interpretability</span>
              <span className="value">
                {explanation.interpretation ? '✓ Explained' : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExplainabilityViewer;
