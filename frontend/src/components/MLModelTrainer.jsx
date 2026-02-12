import React, { useState, useCallback, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
} from 'recharts';
import './MLModelTrainer.css';

const MLModelTrainer = ({ workspaceId, metrics }) => {
  const [trainingState, setTrainingState] = useState({
    status: 'idle', // idle, training, completed, error
    progress: 0,
    trainingId: null,
    model: null,
  });

  const [selectedModel, setSelectedModel] = useState('arima');
  const [trainingResults, setTrainingResults] = useState([]);
  const [selectedResult, setSelectedResult] = useState(null);
  const [hyperparameters, setHyperparameters] = useState({
    arima: { p: 1, d: 1, q: 1 },
    prophet: { seasonality_period: 7 },
    lstm: { sequence_length: 10, hidden_size: 32 },
  });
  const [trainingProgress, setTrainingProgress] = useState([]);
  const [modelComparison, setModelComparison] = useState([]);
  const [socket, setSocket] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState(null);

  // Connect WebSocket
  useEffect(() => {
    const newSocket = io(`http://localhost:5000/ml?workspace_id=${workspaceId}`);
    setSocket(newSocket);

    return () => {
      if (newSocket) newSocket.disconnect();
    };
  }, [workspaceId]);

  // WebSocket listeners
  useEffect(() => {
    if (!socket) return;

    socket.on('training_started', (data) => {
      setTrainingState((prev) => ({
        ...prev,
        status: 'training',
        progress: 0,
        trainingId: data.training_id,
      }));
    });

    socket.on('training_progress', (data) => {
      setTrainingState((prev) => ({
        ...prev,
        progress: data.progress_percent,
      }));
      setTrainingProgress((prev) => [...prev, data]);
    });

    socket.on('training_completed', (data) => {
      setTrainingState((prev) => ({
        ...prev,
        status: 'completed',
        progress: 100,
        model: data.model_id,
      }));
    });

    socket.on('training_metrics', (data) => {
      // Update training metrics in real-time
    });

    socket.on('model_comparison_result', (data) => {
      setModelComparison(data.comparisons || []);
    });

    return () => {
      socket.off('training_started');
      socket.off('training_progress');
      socket.off('training_completed');
      socket.off('training_metrics');
      socket.off('model_comparison_result');
    };
  }, [socket]);

  // Start model training
  const startTraining = useCallback(async () => {
    if (!selectedMetric || !metrics?.[selectedMetric]) {
      alert('Please select a metric');
      return;
    }

    const values = metrics[selectedMetric];
    setTrainingProgress([]);

    // API call
    try {
      const endpoint = `/api/ml/${selectedModel}/train`;
      const response = await fetch(`http://localhost:5000${endpoint}?workspace_id=${workspaceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metric_name: selectedMetric,
          values,
          ...hyperparameters[selectedModel],
        }),
      });

      const result = await response.json();

      // Add to training results
      setTrainingResults((prev) => [...prev, result]);
      setSelectedResult(result);

      // Emit WebSocket event
      if (socket) {
        socket.emit('start_model_training', {
          model_type: selectedModel,
          metric_name: selectedMetric,
          values,
        });
      }
    } catch (error) {
      console.error('Training failed:', error);
      setTrainingState((prev) => ({ ...prev, status: 'error' }));
    }
  }, [selectedMetric, metrics, selectedModel, workspaceId, socket, hyperparameters]);

  // Cancel training
  const cancelTraining = useCallback(() => {
    if (socket && trainingState.trainingId) {
      socket.emit('cancel_training', { training_id: trainingState.trainingId });
      setTrainingState((prev) => ({ ...prev, status: 'idle', progress: 0 }));
    }
  }, [socket, trainingState.trainingId]);

  // Compare models
  const compareModels = useCallback(async () => {
    if (trainingResults.length < 2) {
      alert('Need at least 2 trained models to compare');
      return;
    }

    try {
      const response = await fetch(`http://localhost:5000/api/ml/models/compare?workspace_id=${workspaceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_ids: trainingResults.map((r) => r.model_id),
        }),
      });

      const data = await response.json();
      setModelComparison(data.model_comparisons || []);

      // Emit WebSocket event
      if (socket) {
        socket.emit('model_comparison_update', {
          model_ids: trainingResults.map((r) => r.model_id),
        });
      }
    } catch (error) {
      console.error('Model comparison failed:', error);
    }
  }, [trainingResults, workspaceId, socket]);

  // Render training configuration
  const renderTrainingConfig = () => (
    <div className="training-config">
      <h3>Training Configuration</h3>

      <div className="config-section">
        <label>Metric to Train On</label>
        <select value={selectedMetric || ''} onChange={(e) => setSelectedMetric(e.target.value)}>
          <option value="">-- Select Metric --</option>
          {Object.keys(metrics || {}).map((metric) => (
            <option key={metric} value={metric}>
              {metric.replace(/_/g, ' ')}
            </option>
          ))}
        </select>
      </div>

      <div className="config-section">
        <label>Model Type</label>
        <div className="model-buttons">
          {['arima', 'prophet', 'lstm'].map((model) => (
            <button
              key={model}
              className={`model-btn ${selectedModel === model ? 'active' : ''}`}
              onClick={() => setSelectedModel(model)}
            >
              {model.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="hyperparameters">
        <h4>{selectedModel.toUpperCase()} Hyperparameters</h4>
        {selectedModel === 'arima' && (
          <div className="param-group">
            <div className="param">
              <label>p (AR Order)</label>
              <input
                type="number"
                value={hyperparameters.arima.p}
                onChange={(e) =>
                  setHyperparameters((prev) => ({
                    ...prev,
                    arima: { ...prev.arima, p: +e.target.value },
                  }))
                }
                min="0"
                max="5"
              />
            </div>
            <div className="param">
              <label>d (Differencing)</label>
              <input
                type="number"
                value={hyperparameters.arima.d}
                onChange={(e) =>
                  setHyperparameters((prev) => ({
                    ...prev,
                    arima: { ...prev.arima, d: +e.target.value },
                  }))
                }
                min="0"
                max="2"
              />
            </div>
            <div className="param">
              <label>q (MA Order)</label>
              <input
                type="number"
                value={hyperparameters.arima.q}
                onChange={(e) =>
                  setHyperparameters((prev) => ({
                    ...prev,
                    arima: { ...prev.arima, q: +e.target.value },
                  }))
                }
                min="0"
                max="5"
              />
            </div>
          </div>
        )}

        {selectedModel === 'prophet' && (
          <div className="param-group">
            <div className="param">
              <label>Seasonality Period</label>
              <input
                type="number"
                value={hyperparameters.prophet.seasonality_period}
                onChange={(e) =>
                  setHyperparameters((prev) => ({
                    ...prev,
                    prophet: { ...prev.prophet, seasonality_period: +e.target.value },
                  }))
                }
                min="2"
                max="30"
              />
            </div>
          </div>
        )}

        {selectedModel === 'lstm' && (
          <div className="param-group">
            <div className="param">
              <label>Sequence Length</label>
              <input
                type="number"
                value={hyperparameters.lstm.sequence_length}
                onChange={(e) =>
                  setHyperparameters((prev) => ({
                    ...prev,
                    lstm: { ...prev.lstm, sequence_length: +e.target.value },
                  }))
                }
                min="2"
                max="50"
              />
            </div>
            <div className="param">
              <label>Hidden Size</label>
              <input
                type="number"
                value={hyperparameters.lstm.hidden_size}
                onChange={(e) =>
                  setHyperparameters((prev) => ({
                    ...prev,
                    lstm: { ...prev.lstm, hidden_size: +e.target.value },
                  }))
                }
                min="8"
                max="128"
                step="8"
              />
            </div>
          </div>
        )}
      </div>

      <div className="training-controls">
        <button className="btn btn-primary" onClick={startTraining} disabled={trainingState.status === 'training'}>
          {trainingState.status === 'training' ? 'Training...' : 'Start Training'}
        </button>
        {trainingState.status === 'training' && (
          <button className="btn btn-danger" onClick={cancelTraining}>
            Cancel
          </button>
        )}
      </div>
    </div>
  );

  // Render training progress
  const renderTrainingProgress = () => (
    <div className="training-progress">
      <h3>Training Progress</h3>
      {trainingState.status === 'idle' && <p>No training in progress</p>}
      {trainingState.status === 'training' && (
        <div className="progress-content">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${trainingState.progress}%` }}>
              {trainingState.progress}%
            </div>
          </div>
          <p className="progress-status">Training model: {selectedModel.toUpperCase()}</p>
        </div>
      )}
      {trainingState.status === 'completed' && (
        <div className="completion-message">
          <p>✓ Training completed successfully</p>
          <p>Model ID: {trainingState.model}</p>
        </div>
      )}

      {trainingProgress.length > 0 && (
        <div className="progress-chart">
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={trainingProgress.slice(-10)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="progress_percent"
                stroke="#8884d8"
                name="Progress"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );

  // Render results
  const renderResults = () => (
    <div className="training-results">
      <h3>Trained Models ({trainingResults.length})</h3>

      {trainingResults.length > 0 ? (
        <div>
          <div className="results-list">
            {trainingResults.map((result, idx) => (
              <div
                key={idx}
                className={`result-item ${selectedResult === result ? 'selected' : ''}`}
                onClick={() => setSelectedResult(result)}
              >
                <div className="result-header">
                  <span className="model-type">{result.model_type}</span>
                  <span className={`ready-badge ${result.is_production_ready ? 'ready' : 'not-ready'}`}>
                    {result.is_production_ready ? '✓ Production Ready' : '⚠ Not Ready'}
                  </span>
                </div>
                <div className="result-metrics">
                  <span>R²: {result.metrics.r_squared.toFixed(4)}</span>
                  <span>RMSE: {result.metrics.rmse.toFixed(4)}</span>
                  <span>Accuracy: {result.metrics.forecast_accuracy.toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>

          {selectedResult && (
            <div className="result-details">
              <h4>Model Details</h4>
              <div className="details-grid">
                <div className="detail">
                  <span className="label">Model ID</span>
                  <span className="value">{selectedResult.model_id}</span>
                </div>
                <div className="detail">
                  <span className="label">Type</span>
                  <span className="value">{selectedResult.model_type}</span>
                </div>
                <div className="detail">
                  <span className="label">R² Score</span>
                  <span className="value">{selectedResult.metrics.r_squared.toFixed(4)}</span>
                </div>
                <div className="detail">
                  <span className="label">RMSE</span>
                  <span className="value">{selectedResult.metrics.rmse.toFixed(4)}</span>
                </div>
                <div className="detail">
                  <span className="label">MAPE</span>
                  <span className="value">{selectedResult.metrics.mape.toFixed(2)}%</span>
                </div>
                <div className="detail">
                  <span className="label">Forecast Accuracy</span>
                  <span className="value">{selectedResult.metrics.forecast_accuracy.toFixed(1)}%</span>
                </div>
              </div>

              {selectedResult.cross_validation_scores && (
                <div className="cv-scores">
                  <h4>Cross-Validation Scores</h4>
                  <div className="scores-chart">
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart
                        data={selectedResult.cross_validation_scores.map((score, i) => ({
                          fold: `Fold ${i + 1}`,
                          score: score,
                        }))}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="fold" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="score" fill="#8884d8" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>
          )}

          <button className="btn btn-secondary" onClick={compareModels} disabled={trainingResults.length < 2}>
            Compare All Models
          </button>
        </div>
      ) : (
        <p>No models trained yet</p>
      )}
    </div>
  );

  // Render model comparison
  const renderComparison = () => (
    <div className="model-comparison">
      <h3>Model Comparison</h3>
      {modelComparison.length > 0 ? (
        <div className="comparison-content">
          <div className="comparison-chart">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={modelComparison}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="model_id" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="r_squared" fill="#8884d8" name="R²" />
                <Bar dataKey="rmse" fill="#82ca9d" name="RMSE" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {modelComparison.length > 0 && (
            <div className="best-model">
              <h4>Best Model</h4>
              <div className="best-model-info">
                <p>
                  <strong>{modelComparison[0].model_id}</strong>
                </p>
                <p>R² Score: {modelComparison[0].r_squared.toFixed(4)}</p>
                <p>RMSE: {modelComparison[0].rmse.toFixed(4)}</p>
              </div>
            </div>
          )}
        </div>
      ) : (
        <p>No models to compare</p>
      )}
    </div>
  );

  return (
    <div className="ml-model-trainer">
      <div className="trainer-header">
        <h2>ML Model Trainer</h2>
        <p>Train, evaluate, and compare machine learning models</p>
      </div>

      <div className="trainer-layout">
        <div className="config-panel">
          {renderTrainingConfig()}
        </div>

        <div className="results-panel">
          {renderTrainingProgress()}
          {renderResults()}
          {trainingResults.length > 1 && renderComparison()}
        </div>
      </div>
    </div>
  );
};

export default MLModelTrainer;
