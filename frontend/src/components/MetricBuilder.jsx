/**
 * Phase 23: Metric Builder Component
 * Custom metric creation with formula editor, validation, testing, and publishing
 */

import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import './MetricBuilder.css';

const MetricBuilder = ({ onMetricCreate, onMetricPublish }) => {
  const [step, setStep] = useState(1); // 1: Basic, 2: Formula, 3: Format, 4: Test, 5: Publish
  const [metricData, setMetricData] = useState({
    name: '',
    description: '',
    type: 'simple', // simple, calculated, composite, derived, ml_model
    definition: {},
    formatting: {
      format_type: 'number', // number, currency, percentage, bytes, duration
      decimal_places: 2,
      prefix: '',
      suffix: '',
    },
    thresholds: [
      { label: 'good', min: 0, max: 100, color: '#4CAF50' },
      { label: 'warning', min: 100, max: 150, color: '#FFC107' },
      { label: 'critical', min: 150, max: 1000, color: '#f44336' },
    ],
    targets: {},
    version: 1,
    status: 'draft',
  });

  const [formula, setFormula] = useState('');
  const [formulaError, setFormulaError] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [isTesting, setIsTesting] = useState(false);
  const [previewData, setPreviewData] = useState([]);
  const [selectedField, setSelectedField] = useState('');
  const [availableMetrics, setAvailableMetrics] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load available metrics for calculated/composite types
  useEffect(() => {
    if (['calculated', 'composite', 'derived'].includes(metricData.type)) {
      loadAvailableMetrics();
    }
  }, [metricData.type]);

  const loadAvailableMetrics = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/v1/bi/metrics?limit=100');
      if (response.ok) {
        const data = await response.json();
        setAvailableMetrics(data.metrics || []);
      }
    } catch (err) {
      console.error('Failed to load metrics:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBasicInfoChange = (field, value) => {
    setMetricData({
      ...metricData,
      [field]: value,
    });
  };

  const handleTypeChange = (type) => {
    setMetricData({
      ...metricData,
      type,
      definition: {},
    });
    setFormula('');
    setValidationResult(null);
  };

  const handleFormulaChange = (e) => {
    setFormula(e.target.value);
    setValidationResult(null);
  };

  const handleValidateFormula = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/v1/bi/metrics/validate-formula', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          formula,
          metric_type: metricData.type,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setValidationResult(data);
        setFormulaError(null);
      } else {
        const error = await response.json();
        setFormulaError(error.error);
      }
    } catch (err) {
      setFormulaError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestMetric = async () => {
    try {
      setIsTesting(true);
      const response = await fetch('/api/v1/bi/metrics/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...metricData,
          formula,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setTestResult(data);
        setPreviewData(data.preview_data || []);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsTesting(false);
    }
  };

  const handleFormatChange = (field, value) => {
    setMetricData({
      ...metricData,
      formatting: {
        ...metricData.formatting,
        [field]: value,
      },
    });
  };

  const handleThresholdChange = (index, field, value) => {
    const newThresholds = [...metricData.thresholds];
    newThresholds[index][field] = field === 'label' ? value : parseFloat(value);
    setMetricData({
      ...metricData,
      thresholds: newThresholds,
    });
  };

  const handleTargetChange = (period, value) => {
    setMetricData({
      ...metricData,
      targets: {
        ...metricData.targets,
        [period]: parseFloat(value),
      },
    });
  };

  const handlePublishMetric = async () => {
    try {
      setIsLoading(true);
      const payload = {
        ...metricData,
        formula,
        definition: {
          ...metricData.definition,
          formula,
        },
      };

      const response = await fetch('/api/v1/bi/metrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const data = await response.json();
        setMetricData({
          ...metricData,
          status: 'published',
        });
        if (onMetricPublish) {
          onMetricPublish(data);
        }
        alert(`Metric "${metricData.name}" published successfully!`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const insertMetricReference = (metricName) => {
    setFormula(formula + `[${metricName}]`);
  };

  const insertFunction = (fn) => {
    const functions = {
      sum: 'SUM()',
      avg: 'AVG()',
      min: 'MIN()',
      max: 'MAX()',
      count: 'COUNT()',
      if: 'IF(condition, value_true, value_false)',
    };
    setFormula(formula + functions[fn]);
  };

  const stepTitle = [
    'Metric Basics',
    'Formula Definition',
    'Formatting',
    'Testing & Preview',
    'Review & Publish',
  ];

  return (
    <div className="metric-builder">
      {/* Header */}
      <div className="metric-builder__header">
        <h1 className="metric-builder__title">Create Custom Metric</h1>
        <div className="metric-builder__steps">
          {stepTitle.map((title, index) => (
            <div
              key={index + 1}
              className={`metric-builder__step ${
                step === index + 1 ? 'active' : ''
              } ${step > index + 1 ? 'completed' : ''}`}
              onClick={() => step > index + 1 && setStep(index + 1)}
            >
              <div className="metric-builder__step-number">{index + 1}</div>
              <div className="metric-builder__step-label">{title}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="metric-builder__error">
          <button onClick={() => setError(null)} className="metric-builder__error-close">✕</button>
          {error}
        </div>
      )}

      {/* Step 1: Basic Information */}
      {step === 1 && (
        <div className="metric-builder__step-content">
          <div className="metric-builder__form-group">
            <label className="metric-builder__label">Metric Name *</label>
            <input
              type="text"
              className="metric-builder__input"
              value={metricData.name}
              onChange={(e) => handleBasicInfoChange('name', e.target.value)}
              placeholder="e.g., Revenue Per User"
            />
          </div>

          <div className="metric-builder__form-group">
            <label className="metric-builder__label">Description</label>
            <textarea
              className="metric-builder__textarea"
              value={metricData.description}
              onChange={(e) => handleBasicInfoChange('description', e.target.value)}
              placeholder="Describe what this metric measures"
              rows={4}
            />
          </div>

          <div className="metric-builder__form-group">
            <label className="metric-builder__label">Metric Type *</label>
            <div className="metric-builder__radio-group">
              {['simple', 'calculated', 'composite', 'derived', 'ml_model'].map(type => (
                <label key={type} className="metric-builder__radio">
                  <input
                    type="radio"
                    name="metric-type"
                    value={type}
                    checked={metricData.type === type}
                    onChange={() => handleTypeChange(type)}
                  />
                  <span className="metric-builder__radio-label">
                    {type === 'simple' && 'Simple (Single Field Aggregation)'}
                    {type === 'calculated' && 'Calculated (Formula-based)'}
                    {type === 'composite' && 'Composite (Multiple Metrics)'}
                    {type === 'derived' && 'Derived (From Other Metrics)'}
                    {type === 'ml_model' && 'ML Model (Predictive)'}
                  </span>
                </label>
              ))}
            </div>
          </div>

          <div className="metric-builder__actions">
            <button
              className="metric-builder__btn metric-builder__btn--next"
              onClick={() => {
                if (metricData.name.trim()) {
                  setStep(2);
                } else {
                  setError('Metric name is required');
                }
              }}
            >
              Next →
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Formula Definition */}
      {step === 2 && (
        <div className="metric-builder__step-content">
          {metricData.type === 'simple' && (
            <div className="metric-builder__form-group">
              <label className="metric-builder__label">Field & Aggregation</label>
              <div className="metric-builder__select-group">
                <select
                  className="metric-builder__select"
                  onChange={(e) => setFormula(e.target.value)}
                >
                  <option value="">Select field...</option>
                  <option value="SUM(revenue)">SUM(revenue)</option>
                  <option value="AVG(order_value)">AVG(order_value)</option>
                  <option value="COUNT(*)">COUNT(*)</option>
                  <option value="COUNT(DISTINCT user_id)">COUNT(DISTINCT user_id)</option>
                </select>
              </div>
            </div>
          )}

          {['calculated', 'composite', 'derived'].includes(metricData.type) && (
            <>
              <div className="metric-builder__form-group">
                <label className="metric-builder__label">Formula *</label>
                <textarea
                  className={`metric-builder__formula-editor ${
                    formulaError ? 'error' : ''
                  }`}
                  value={formula}
                  onChange={handleFormulaChange}
                  placeholder="e.g., (revenue - cost) / revenue * 100"
                  rows={6}
                />
                {formulaError && (
                  <div className="metric-builder__error-message">{formulaError}</div>
                )}
              </div>

              <div className="metric-builder__formula-helpers">
                <div className="metric-builder__helper-section">
                  <h4 className="metric-builder__helper-title">Functions</h4>
                  <div className="metric-builder__helper-buttons">
                    {['sum', 'avg', 'min', 'max', 'count', 'if'].map(fn => (
                      <button
                        key={fn}
                        className="metric-builder__helper-btn"
                        onClick={() => insertFunction(fn)}
                      >
                        {fn.toUpperCase()}()
                      </button>
                    ))}
                  </div>
                </div>

                {availableMetrics.length > 0 && (
                  <div className="metric-builder__helper-section">
                    <h4 className="metric-builder__helper-title">Available Metrics</h4>
                    <div className="metric-builder__metric-list">
                      {availableMetrics.slice(0, 5).map(metric => (
                        <button
                          key={metric.id}
                          className="metric-builder__metric-ref"
                          onClick={() => insertMetricReference(metric.name)}
                        >
                          [{metric.name}]
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          {validationResult && (
            <div className="metric-builder__validation-result">
              <div className={`metric-builder__validation-badge ${
                validationResult.valid ? 'success' : 'error'
              }`}>
                {validationResult.valid ? '✓ Valid Formula' : '✗ Invalid Formula'}
              </div>
              {validationResult.dependencies && (
                <div className="metric-builder__dependencies">
                  <strong>Dependencies:</strong>
                  <ul>
                    {validationResult.dependencies.map((dep, i) => (
                      <li key={i}>{dep}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          <div className="metric-builder__actions">
            <button
              className="metric-builder__btn metric-builder__btn--secondary"
              onClick={() => setStep(1)}
            >
              ← Back
            </button>
            <button
              className="metric-builder__btn"
              onClick={handleValidateFormula}
              disabled={!formula || isLoading}
            >
              {isLoading ? 'Validating...' : 'Validate Formula'}
            </button>
            <button
              className="metric-builder__btn metric-builder__btn--next"
              onClick={() => setStep(3)}
              disabled={!validationResult?.valid}
            >
              Next →
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Formatting */}
      {step === 3 && (
        <div className="metric-builder__step-content">
          <div className="metric-builder__form-group">
            <label className="metric-builder__label">Format Type</label>
            <select
              className="metric-builder__select"
              value={metricData.formatting.format_type}
              onChange={(e) => handleFormatChange('format_type', e.target.value)}
            >
              <option value="number">Number</option>
              <option value="currency">Currency</option>
              <option value="percentage">Percentage</option>
              <option value="bytes">Bytes (KB, MB, GB)</option>
              <option value="duration">Duration (hours, minutes)</option>
            </select>
          </div>

          <div className="metric-builder__form-row">
            <div className="metric-builder__form-group">
              <label className="metric-builder__label">Decimal Places</label>
              <input
                type="number"
                className="metric-builder__input"
                value={metricData.formatting.decimal_places}
                onChange={(e) => handleFormatChange('decimal_places', e.target.value)}
                min="0"
                max="10"
              />
            </div>

            <div className="metric-builder__form-group">
              <label className="metric-builder__label">Prefix</label>
              <input
                type="text"
                className="metric-builder__input"
                value={metricData.formatting.prefix}
                onChange={(e) => handleFormatChange('prefix', e.target.value)}
                placeholder="e.g., $"
              />
            </div>

            <div className="metric-builder__form-group">
              <label className="metric-builder__label">Suffix</label>
              <input
                type="text"
                className="metric-builder__input"
                value={metricData.formatting.suffix}
                onChange={(e) => handleFormatChange('suffix', e.target.value)}
                placeholder="e.g., %"
              />
            </div>
          </div>

          <div className="metric-builder__form-group">
            <label className="metric-builder__label">Status Thresholds</label>
            <div className="metric-builder__thresholds">
              {metricData.thresholds.map((threshold, index) => (
                <div key={index} className="metric-builder__threshold">
                  <input
                    type="text"
                    className="metric-builder__threshold-label"
                    value={threshold.label}
                    onChange={(e) => handleThresholdChange(index, 'label', e.target.value)}
                    placeholder="Label"
                  />
                  <div className="metric-builder__threshold-range">
                    <input
                      type="number"
                      className="metric-builder__threshold-input"
                      value={threshold.min}
                      onChange={(e) => handleThresholdChange(index, 'min', e.target.value)}
                      placeholder="Min"
                    />
                    <span className="metric-builder__threshold-dash">-</span>
                    <input
                      type="number"
                      className="metric-builder__threshold-input"
                      value={threshold.max}
                      onChange={(e) => handleThresholdChange(index, 'max', e.target.value)}
                      placeholder="Max"
                    />
                  </div>
                  <input
                    type="color"
                    className="metric-builder__color-picker"
                    value={threshold.color}
                    onChange={(e) => handleThresholdChange(index, 'color', e.target.value)}
                  />
                  <span className="metric-builder__color-swatch" style={{
                    backgroundColor: threshold.color,
                  }} />
                </div>
              ))}
            </div>
          </div>

          <div className="metric-builder__actions">
            <button
              className="metric-builder__btn metric-builder__btn--secondary"
              onClick={() => setStep(2)}
            >
              ← Back
            </button>
            <button
              className="metric-builder__btn metric-builder__btn--next"
              onClick={() => setStep(4)}
            >
              Next →
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Testing */}
      {step === 4 && (
        <div className="metric-builder__step-content">
          <div className="metric-builder__test-info">
            <h3>Test Your Metric</h3>
            <p>Run a test to verify the metric calculates correctly</p>
          </div>

          <button
            className="metric-builder__btn"
            onClick={handleTestMetric}
            disabled={isTesting || isLoading}
          >
            {isTesting ? 'Testing...' : 'Run Test'}
          </button>

          {testResult && (
            <div className="metric-builder__test-result">
              <div className={`metric-builder__test-badge ${
                testResult.passed ? 'success' : 'error'
              }`}>
                {testResult.passed ? '✓ Test Passed' : '✗ Test Failed'}
              </div>
              <div className="metric-builder__test-details">
                <div className="metric-builder__detail">
                  <span className="metric-builder__detail-label">Sample Value:</span>
                  <span className="metric-builder__detail-value">
                    {testResult.sample_value}
                  </span>
                </div>
                <div className="metric-builder__detail">
                  <span className="metric-builder__detail-label">Calculation Time:</span>
                  <span className="metric-builder__detail-value">
                    {testResult.calculation_time_ms}ms
                  </span>
                </div>
              </div>

              {previewData.length > 0 && (
                <div className="metric-builder__preview">
                  <h4>Data Preview</h4>
                  <table className="metric-builder__preview-table">
                    <tbody>
                      {previewData.slice(0, 5).map((row, i) => (
                        <tr key={i}>
                          <td>{row.value}</td>
                          <td>{row.date}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          <div className="metric-builder__actions">
            <button
              className="metric-builder__btn metric-builder__btn--secondary"
              onClick={() => setStep(3)}
            >
              ← Back
            </button>
            <button
              className="metric-builder__btn metric-builder__btn--next"
              onClick={() => setStep(5)}
              disabled={!testResult?.passed}
            >
              Next →
            </button>
          </div>
        </div>
      )}

      {/* Step 5: Review & Publish */}
      {step === 5 && (
        <div className="metric-builder__step-content">
          <div className="metric-builder__review">
            <h3>Review Metric Configuration</h3>

            <div className="metric-builder__review-section">
              <h4>Basic Information</h4>
              <dl>
                <dt>Name:</dt>
                <dd>{metricData.name}</dd>
                <dt>Type:</dt>
                <dd>{metricData.type}</dd>
                <dt>Description:</dt>
                <dd>{metricData.description || '—'}</dd>
              </dl>
            </div>

            <div className="metric-builder__review-section">
              <h4>Formula</h4>
              <code className="metric-builder__formula-display">{formula}</code>
            </div>

            <div className="metric-builder__review-section">
              <h4>Formatting</h4>
              <dl>
                <dt>Format:</dt>
                <dd>{metricData.formatting.format_type}</dd>
                <dt>Decimal Places:</dt>
                <dd>{metricData.formatting.decimal_places}</dd>
                <dt>Prefix/Suffix:</dt>
                <dd>{metricData.formatting.prefix || '—'} / {metricData.formatting.suffix || '—'}</dd>
              </dl>
            </div>
          </div>

          <div className="metric-builder__actions">
            <button
              className="metric-builder__btn metric-builder__btn--secondary"
              onClick={() => setStep(4)}
            >
              ← Back
            </button>
            <button
              className="metric-builder__btn metric-builder__btn--publish"
              onClick={handlePublishMetric}
              disabled={isLoading}
            >
              {isLoading ? 'Publishing...' : '✓ Publish Metric'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

MetricBuilder.propTypes = {
  onMetricCreate: PropTypes.func,
  onMetricPublish: PropTypes.func,
};

export default MetricBuilder;
