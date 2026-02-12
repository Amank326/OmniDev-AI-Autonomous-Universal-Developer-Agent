import React, { useState, useEffect, useCallback } from 'react';
import './AlertConfigManager.css';

const AlertConfigManager = ({ workspaceId, onAlertCreated, onAlertDeleted }) => {
  const [alerts, setAlerts] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingAlert, setEditingAlert] = useState(null);
  const [loadingAlerts, setLoadingAlerts] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all'); // all, enabled, disabled
  const [formData, setFormData] = useState({
    alert_name: '',
    metric_name: '',
    threshold: '',
    comparison_operator: 'greater_than',
    window_size: 5,
    forecast_threshold: '',
    enabled: true,
    severity: 'high',
    notification_channels: [],
    description: '',
  });
  const [validationErrors, setValidationErrors] = useState({});

  // Available metrics
  const metrics = [
    'execution_time',
    'error_rate',
    'throughput',
    'resource_usage',
    'agent_load',
    'task_completion_rate',
    'api_latency',
    'database_queries',
  ];

  const operators = [
    { id: 'greater_than', label: 'Greater Than (>)' },
    { id: 'less_than', label: 'Less Than (<)' },
    { id: 'equals', label: 'Equals (=)' },
    { id: 'not_equals', label: 'Not Equals (≠)' },
    { id: 'greater_equal', label: 'Greater or Equal (≥)' },
    { id: 'less_equal', label: 'Less or Equal (≤)' },
  ];

  const notificationChannels = [
    { id: 'email', label: '📧 Email' },
    { id: 'slack', label: '💬 Slack' },
    { id: 'webhook', label: '🔗 Webhook' },
    { id: 'pagerduty', label: '🚨 PagerDuty' },
    { id: 'sms', label: '📱 SMS' },
  ];

  // Fetch alerts
  const fetchAlerts = useCallback(async () => {
    setLoadingAlerts(true);
    try {
      // Mock API call
      const response = await new Promise(resolve => {
        setTimeout(() => {
          resolve([
            {
              id: 'alert_1',
              alert_name: 'High Execution Time',
              metric_name: 'execution_time',
              threshold: 200,
              comparison_operator: 'greater_than',
              window_size: 5,
              forecast_threshold: 250,
              enabled: true,
              severity: 'high',
              created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
              triggered_count: 3,
              last_triggered: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
              notification_channels: ['email', 'slack'],
              description: 'Alert when execution time exceeds 200ms',
            },
            {
              id: 'alert_2',
              alert_name: 'High Error Rate',
              metric_name: 'error_rate',
              threshold: 0.05,
              comparison_operator: 'greater_than',
              window_size: 10,
              forecast_threshold: 0.08,
              enabled: true,
              severity: 'critical',
              created_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
              triggered_count: 1,
              last_triggered: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
              notification_channels: ['email', 'pagerduty', 'slack'],
              description: 'Alert when error rate exceeds 5%',
            },
            {
              id: 'alert_3',
              alert_name: 'Low Throughput',
              metric_name: 'throughput',
              threshold: 100,
              comparison_operator: 'less_than',
              window_size: 5,
              forecast_threshold: 80,
              enabled: false,
              severity: 'medium',
              created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
              triggered_count: 0,
              last_triggered: null,
              notification_channels: ['email'],
              description: 'Alert when throughput drops below 100 ops/s',
            },
          ]);
        }, 500);
      });

      setAlerts(response);
    } catch (error) {
      console.error('Alerts fetch error:', error);
    } finally {
      setLoadingAlerts(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  // Validate form
  const validateForm = () => {
    const errors = {};

    if (!formData.alert_name.trim()) {
      errors.alert_name = 'Alert name is required';
    }
    if (!formData.metric_name) {
      errors.metric_name = 'Metric is required';
    }
    if (formData.threshold === '' || formData.threshold === null) {
      errors.threshold = 'Threshold is required';
    }
    if (formData.forecast_threshold === '' && formData.forecast_threshold !== null) {
      // Optional field, but if provided must be valid
      if (isNaN(parseFloat(formData.forecast_threshold))) {
        errors.forecast_threshold = 'Must be a valid number';
      }
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Handle form submit
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      const newAlert = {
        id: editingAlert?.id || `alert_${Date.now()}`,
        ...formData,
        threshold: parseFloat(formData.threshold),
        forecast_threshold: formData.forecast_threshold ? parseFloat(formData.forecast_threshold) : null,
        created_at: editingAlert?.created_at || new Date().toISOString(),
        last_triggered: editingAlert?.last_triggered || null,
        triggered_count: editingAlert?.triggered_count || 0,
      };

      if (editingAlert) {
        // Update existing alert
        setAlerts(alerts.map(a => a.id === editingAlert.id ? newAlert : a));
      } else {
        // Create new alert
        setAlerts([...alerts, newAlert]);
        if (onAlertCreated) {
          onAlertCreated(newAlert);
        }
      }

      // Reset form
      resetForm();
      setShowCreateForm(false);
    } catch (error) {
      console.error('Error saving alert:', error);
    }
  };

  // Reset form
  const resetForm = () => {
    setFormData({
      alert_name: '',
      metric_name: '',
      threshold: '',
      comparison_operator: 'greater_than',
      window_size: 5,
      forecast_threshold: '',
      enabled: true,
      severity: 'high',
      notification_channels: [],
      description: '',
    });
    setValidationErrors({});
    setEditingAlert(null);
  };

  // Handle delete
  const handleDelete = async (alertId) => {
    if (window.confirm('Are you sure you want to delete this alert?')) {
      setAlerts(alerts.filter(a => a.id !== alertId));
      if (onAlertDeleted) {
        onAlertDeleted(alertId);
      }
    }
  };

  // Handle edit
  const handleEdit = (alert) => {
    setFormData(alert);
    setEditingAlert(alert);
    setShowCreateForm(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Handle toggle enable/disable
  const handleToggleEnabled = (alertId) => {
    setAlerts(alerts.map(a => 
      a.id === alertId ? { ...a, enabled: !a.enabled } : a
    ));
  };

  // Handle notification channel toggle
  const toggleNotificationChannel = (channel) => {
    setFormData(prev => ({
      ...prev,
      notification_channels: prev.notification_channels.includes(channel)
        ? prev.notification_channels.filter(c => c !== channel)
        : [...prev.notification_channels, channel],
    }));
  };

  // Filtered alerts
  const filteredAlerts = alerts.filter(alert => {
    if (filterStatus === 'enabled') return alert.enabled;
    if (filterStatus === 'disabled') return !alert.enabled;
    return true;
  });

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return '#d9534f';
      case 'high':
        return '#f0ad4e';
      case 'medium':
        return '#5bc0de';
      case 'low':
        return '#5cb85c';
      default:
        return '#6c757d';
    }
  };

  return (
    <div className="alert-config-manager">
      <div className="manager-header">
        <h1>🔔 Alert Configuration Manager</h1>
        <button
          className="btn-create-alert"
          onClick={() => {
            resetForm();
            setShowCreateForm(true);
          }}
        >
          + Create New Alert
        </button>
      </div>

      {/* Create/Edit Form */}
      {showCreateForm && (
        <div className="alert-form-container">
          <div className="form-header">
            <h2>{editingAlert ? 'Edit Alert' : 'Create New Alert'}</h2>
            <button
              className="btn-close"
              onClick={() => {
                setShowCreateForm(false);
                resetForm();
              }}
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleSubmit} className="alert-form">
            {/* Basic Info */}
            <fieldset className="form-section">
              <legend>Basic Information</legend>

              <div className="form-group">
                <label>Alert Name *</label>
                <input
                  type="text"
                  value={formData.alert_name}
                  onChange={(e) => setFormData({ ...formData, alert_name: e.target.value })}
                  placeholder="e.g., High Execution Time"
                  className={validationErrors.alert_name ? 'error' : ''}
                />
                {validationErrors.alert_name && (
                  <span className="error-message">{validationErrors.alert_name}</span>
                )}
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe the purpose of this alert..."
                  rows="2"
                />
              </div>
            </fieldset>

            {/* Metric & Threshold */}
            <fieldset className="form-section">
              <legend>Metric Configuration</legend>

              <div className="form-grid">
                <div className="form-group">
                  <label>Metric *</label>
                  <select
                    value={formData.metric_name}
                    onChange={(e) => setFormData({ ...formData, metric_name: e.target.value })}
                    className={validationErrors.metric_name ? 'error' : ''}
                  >
                    <option value="">Select a metric</option>
                    {metrics.map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                  {validationErrors.metric_name && (
                    <span className="error-message">{validationErrors.metric_name}</span>
                  )}
                </div>

                <div className="form-group">
                  <label>Comparison Operator</label>
                  <select
                    value={formData.comparison_operator}
                    onChange={(e) => setFormData({ ...formData, comparison_operator: e.target.value })}
                  >
                    {operators.map(op => (
                      <option key={op.id} value={op.id}>{op.label}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Threshold Value *</label>
                  <input
                    type="number"
                    step="any"
                    value={formData.threshold}
                    onChange={(e) => setFormData({ ...formData, threshold: e.target.value })}
                    placeholder="e.g., 200"
                    className={validationErrors.threshold ? 'error' : ''}
                  />
                  {validationErrors.threshold && (
                    <span className="error-message">{validationErrors.threshold}</span>
                  )}
                </div>

                <div className="form-group">
                  <label>Window Size (samples)</label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={formData.window_size}
                    onChange={(e) => setFormData({ ...formData, window_size: parseInt(e.target.value) })}
                  />
                </div>

                <div className="form-group">
                  <label>Forecast Threshold (optional)</label>
                  <input
                    type="number"
                    step="any"
                    value={formData.forecast_threshold}
                    onChange={(e) => setFormData({ ...formData, forecast_threshold: e.target.value })}
                    placeholder="Alert if prediction exceeds this"
                  />
                </div>

                <div className="form-group">
                  <label>Severity</label>
                  <select
                    value={formData.severity}
                    onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>
            </fieldset>

            {/* Notification Channels */}
            <fieldset className="form-section">
              <legend>Notification Channels</legend>

              <div className="channels-grid">
                {notificationChannels.map(channel => (
                  <label key={channel.id} className="channel-checkbox">
                    <input
                      type="checkbox"
                      checked={formData.notification_channels.includes(channel.id)}
                      onChange={() => toggleNotificationChannel(channel.id)}
                    />
                    <span>{channel.label}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            {/* Status */}
            <fieldset className="form-section">
              <legend>Status</legend>

              <label className="status-checkbox">
                <input
                  type="checkbox"
                  checked={formData.enabled}
                  onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                />
                <span>Enable this alert</span>
              </label>
            </fieldset>

            {/* Form Actions */}
            <div className="form-actions">
              <button type="submit" className="btn-save">
                {editingAlert ? 'Update Alert' : 'Create Alert'}
              </button>
              <button
                type="button"
                className="btn-cancel"
                onClick={() => {
                  setShowCreateForm(false);
                  resetForm();
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Alerts List */}
      <div className="alerts-section">
        <div className="alerts-toolbar">
          <h2>Configured Alerts ({filteredAlerts.length})</h2>
          <div className="filter-controls">
            <label>Filter:</label>
            <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
              <option value="all">All Alerts</option>
              <option value="enabled">Enabled Only</option>
              <option value="disabled">Disabled Only</option>
            </select>
          </div>
        </div>

        {loadingAlerts ? (
          <div className="loading">Loading alerts...</div>
        ) : filteredAlerts.length === 0 ? (
          <div className="empty-state">
            <p>No alerts configured yet.</p>
            <button onClick={() => setShowCreateForm(true)} className="btn-create-inline">
              Create your first alert
            </button>
          </div>
        ) : (
          <div className="alerts-list">
            {filteredAlerts.map(alert => (
              <div key={alert.id} className={`alert-card ${!alert.enabled ? 'disabled' : ''}`}>
                <div className="alert-card-header">
                  <div className="alert-title-group">
                    <h3>{alert.alert_name}</h3>
                    <span
                      className="severity-badge"
                      style={{ backgroundColor: getSeverityColor(alert.severity) }}
                    >
                      {alert.severity.toUpperCase()}
                    </span>
                    <span className={`status-badge ${alert.enabled ? 'enabled' : 'disabled'}`}>
                      {alert.enabled ? '● ENABLED' : '○ DISABLED'}
                    </span>
                  </div>

                  <div className="alert-actions">
                    <button
                      className="action-btn edit"
                      onClick={() => handleEdit(alert)}
                      title="Edit alert"
                    >
                      ✎
                    </button>
                    <button
                      className="action-btn toggle"
                      onClick={() => handleToggleEnabled(alert.id)}
                      title={alert.enabled ? 'Disable alert' : 'Enable alert'}
                    >
                      {alert.enabled ? '⊘' : '⊙'}
                    </button>
                    <button
                      className="action-btn delete"
                      onClick={() => handleDelete(alert.id)}
                      title="Delete alert"
                    >
                      🗑
                    </button>
                  </div>
                </div>

                <div className="alert-details">
                  <div className="detail-row">
                    <span className="detail-label">Metric:</span>
                    <span className="detail-value">{alert.metric_name}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Condition:</span>
                    <span className="detail-value">
                      {alert.comparison_operator} {alert.threshold}
                      {alert.forecast_threshold && ` (forecast: ${alert.forecast_threshold})`}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Window:</span>
                    <span className="detail-value">{alert.window_size} samples</span>
                  </div>
                </div>

                <div className="alert-notifications">
                  <strong>Notifies via:</strong>
                  <div className="channel-badges">
                    {alert.notification_channels.length > 0 ? (
                      alert.notification_channels.map(channel => (
                        <span key={channel} className="channel-badge">
                          {notificationChannels.find(c => c.id === channel)?.label}
                        </span>
                      ))
                    ) : (
                      <span className="no-channels">No channels configured</span>
                    )}
                  </div>
                </div>

                <div className="alert-statistics">
                  <div className="stat">
                    <label>Triggered:</label>
                    <span>{alert.triggered_count} times</span>
                  </div>
                  <div className="stat">
                    <label>Last Triggered:</label>
                    <span>
                      {alert.last_triggered
                        ? new Date(alert.last_triggered).toLocaleString()
                        : 'Never'}
                    </span>
                  </div>
                  <div className="stat">
                    <label>Created:</label>
                    <span>{new Date(alert.created_at).toLocaleString()}</span>
                  </div>
                </div>

                {alert.description && (
                  <div className="alert-description">
                    <strong>Description:</strong> {alert.description}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertConfigManager;
