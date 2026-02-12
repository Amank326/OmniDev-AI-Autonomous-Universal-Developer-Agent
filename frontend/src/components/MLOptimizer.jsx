import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import './MLOptimizer.css';

const MLOptimizer = ({ workspaceId, refreshInterval = 5000 }) => {
  const [actions, setActions] = useState([]);
  const [executionHistory, setExecutionHistory] = useState([]);
  const [scheduledActions, setScheduledActions] = useState([]);
  const [activeTab, setActiveTab] = useState('queue');
  const [selectedAction, setSelectedAction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ status: 'all', riskLevel: 'all', actionType: 'all' });
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [scheduleData, setScheduleData] = useState({ date: '', time: '', description: '' });

  // Fetch optimization actions
  useEffect(() => {
    const fetchActions = async () => {
      try {
        const response = await fetch('/api/v1/ml_advanced/automation/actions?limit=50', {
          headers: { 'X-Workspace-ID': workspaceId },
        });
        const data = await response.json();
        if (data.success) {
          setActions(data.actions);
          setLoading(false);
        }
      } catch (error) {
        console.error('Failed to fetch actions:', error);
        setLoading(false);
      }
    };

    fetchActions();
    const interval = setInterval(fetchActions, refreshInterval);
    return () => clearInterval(interval);
  }, [workspaceId, refreshInterval]);

  // Fetch execution history
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch('/api/v1/ml_advanced/automation/actions?limit=100&status=completed', {
          headers: { 'X-Workspace-ID': workspaceId },
        });
        const data = await response.json();
        if (data.success) {
          setExecutionHistory(data.actions);
        }
      } catch (error) {
        console.error('Failed to fetch execution history:', error);
      }
    };

    if (activeTab === 'history') {
      fetchHistory();
    }
  }, [workspaceId, activeTab]);

  // Execute action
  const handleExecuteAction = async (action) => {
    try {
      const response = await fetch('/api/v1/ml_advanced/automation/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Workspace-ID': workspaceId,
        },
        body: JSON.stringify({
          action_id: action.action_id,
          action: action,
        }),
      });
      const data = await response.json();
      if (data.success) {
        // Update action status
        setActions((prev) =>
          prev.map((a) =>
            a.action_id === action.action_id ? { ...a, status: 'executing' } : a
          )
        );
      }
    } catch (error) {
      console.error('Failed to execute action:', error);
    }
  };

  // Schedule action
  const handleScheduleAction = (action) => {
    setSelectedAction(action);
    setShowScheduleModal(true);
  };

  const confirmSchedule = async () => {
    try {
      const response = await fetch('/api/v1/ml_advanced/automation/actions/schedule', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Workspace-ID': workspaceId,
        },
        body: JSON.stringify({
          action_id: selectedAction.action_id,
          scheduled_time: `${scheduleData.date}T${scheduleData.time}`,
          description: scheduleData.description,
        }),
      });
      const data = await response.json();
      if (data.success) {
        setScheduledActions((prev) => [...prev, data.scheduled_action]);
        setShowScheduleModal(false);
        setScheduleData({ date: '', time: '', description: '' });
      }
    } catch (error) {
      console.error('Failed to schedule action:', error);
    }
  };

  // Filter actions
  const filteredActions = actions.filter((action) => {
    if (filters.status !== 'all' && action.status !== filters.status) return false;
    if (filters.riskLevel !== 'all' && action.risk_level !== filters.riskLevel) return false;
    if (filters.actionType !== 'all' && action.action_type !== filters.actionType) return false;
    return true;
  });

  // Risk level color mapping
  const getRiskColor = (riskLevel) => {
    const colors = {
      critical: '#ef4444',
      high: '#f97316',
      medium: '#eab308',
      low: '#22c55e',
    };
    return colors[riskLevel] || '#6b7280';
  };

  // Status color mapping
  const getStatusColor = (status) => {
    const colors = {
      pending: '#9ca3af',
      approved: '#3b82f6',
      executing: '#f59e0b',
      completed: '#22c55e',
      failed: '#ef4444',
    };
    return colors[status] || '#6b7280';
  };

  // Action Queue View
  const ActionQueueView = () => (
    <div className="action-queue-view">
      <h2>Optimization Action Queue</h2>

      {/* Filters */}
      <div className="filter-bar">
        <div className="filter-group">
          <label>Status:</label>
          <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="executing">Executing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Risk Level:</label>
          <select value={filters.riskLevel} onChange={(e) => setFilters({ ...filters, riskLevel: e.target.value })}>
            <option value="all">All</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Type:</label>
          <select value={filters.actionType} onChange={(e) => setFilters({ ...filters, actionType: e.target.value })}>
            <option value="all">All</option>
            <option value="scale">Scale</option>
            <option value="optimize">Optimize</option>
            <option value="repair">Repair</option>
            <option value="config">Config</option>
          </select>
        </div>
      </div>

      {/* Action List */}
      <div className="action-list">
        {filteredActions.length > 0 ? (
          filteredActions.map((action, idx) => (
            <div
              key={idx}
              className={`action-item ${action.status} ${selectedAction?.action_id === action.action_id ? 'selected' : ''}`}
              onClick={() => setSelectedAction(action)}
            >
              <div className="action-header">
                <div className="action-title">
                  <h3>{action.action_type.toUpperCase()}</h3>
                  <span className="action-id">ID: {action.action_id.substring(0, 8)}</span>
                </div>
                <div className="action-badges">
                  <span className="status-badge" style={{ backgroundColor: getStatusColor(action.status) }}>
                    {action.status.toUpperCase()}
                  </span>
                  <span className="risk-badge" style={{ backgroundColor: getRiskColor(action.risk_level) }}>
                    {action.risk_level.toUpperCase()}
                  </span>
                </div>
              </div>

              <p className="description">{action.description}</p>

              <div className="action-details">
                <div className="detail">
                  <span className="label">Impact:</span>
                  <span className="value">{action.impact_metric}</span>
                </div>
                <div className="detail">
                  <span className="label">Est. Savings:</span>
                  <span className="value">${action.estimated_savings}</span>
                </div>
                <div className="detail">
                  <span className="label">Priority:</span>
                  <span className="value">{action.priority || 'N/A'}</span>
                </div>
              </div>

              {selectedAction?.action_id === action.action_id && (
                <div className="action-controls">
                  {action.status === 'pending' && (
                    <>
                      <button className="action-btn approve" onClick={() => handleExecuteAction(action)}>
                        Execute Now
                      </button>
                      <button className="action-btn schedule" onClick={() => handleScheduleAction(action)}>
                        Schedule
                      </button>
                    </>
                  )}
                  {action.status === 'approved' && (
                    <button className="action-btn execute" onClick={() => handleExecuteAction(action)}>
                      Start Execution
                    </button>
                  )}
                  {['executing', 'completed', 'failed'].includes(action.status) && (
                    <button className="action-btn view" onClick={() => setActiveTab('history')}>
                      View Details
                    </button>
                  )}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="empty-state">No actions match your filters</div>
        )}
      </div>
    </div>
  );

  // Scheduler View
  const SchedulerView = () => (
    <div className="scheduler-view">
      <h2>Scheduled Actions</h2>
      <div className="scheduled-grid">
        {scheduledActions.length > 0 ? (
          scheduledActions.map((scheduled, idx) => (
            <div key={idx} className="scheduled-card">
              <div className="scheduled-header">
                <h3>{scheduled.action_type}</h3>
                <span className="scheduled-time">{new Date(scheduled.scheduled_time).toLocaleString()}</span>
              </div>
              <p className="description">{scheduled.description}</p>
              <div className="countdown">
                <span>Scheduled in {Math.ceil((new Date(scheduled.scheduled_time) - new Date()) / 60000)} minutes</span>
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state">No scheduled actions</div>
        )}
      </div>
    </div>
  );

  // Impact Dashboard View
  const ImpactDashboardView = () => {
    // Group actions by type for pie chart
    const actionTypeCounts = actions.reduce((acc, action) => {
      const existing = acc.find((a) => a.name === action.action_type);
      if (existing) {
        existing.value += 1;
      } else {
        acc.push({ name: action.action_type, value: 1 });
      }
      return acc;
    }, []);

    const typeColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

    // Calculate impact metrics
    const totalSavings = actions.reduce((sum, action) => sum + (action.estimated_savings || 0), 0);
    const riskDistribution = actions.reduce((acc, action) => {
      const existing = acc.find((a) => a.name === action.risk_level);
      if (existing) {
        existing.count += 1;
      } else {
        acc.push({ name: action.risk_level, count: 1 });
      }
      return acc;
    }, []);

    return (
      <div className="impact-dashboard">
        <h2>Impact & ROI Analysis</h2>

        {/* Metrics Cards */}
        <div className="metrics-grid">
          <div className="metric-card">
            <span className="metric-label">Total Est. Savings</span>
            <span className="metric-value">${totalSavings.toLocaleString()}</span>
          </div>
          <div className="metric-card">
            <span className="metric-label">Pending Actions</span>
            <span className="metric-value">{actions.filter((a) => a.status === 'pending').length}</span>
          </div>
          <div className="metric-card">
            <span className="metric-label">In Progress</span>
            <span className="metric-value">{actions.filter((a) => a.status === 'executing').length}</span>
          </div>
          <div className="metric-card">
            <span className="metric-label">Completed</span>
            <span className="metric-value">{actions.filter((a) => a.status === 'completed').length}</span>
          </div>
        </div>

        {/* Charts */}
        <div className="charts-grid">
          <div className="chart-container">
            <h3>Actions by Type</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={actionTypeCounts}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {actionTypeCounts.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={typeColors[index % typeColors.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Risk Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={riskDistribution}
                margin={{ top: 20, right: 30, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    );
  };

  // Execution History View
  const HistoryView = () => (
    <div className="history-view">
      <h2>Execution History</h2>
      <div className="history-list">
        {executionHistory.length > 0 ? (
          executionHistory.map((history, idx) => (
            <div key={idx} className={`history-item ${history.status}`}>
              <div className="history-header">
                <h3>{history.action_type}</h3>
                <span
                  className="status-badge"
                  style={{ backgroundColor: getStatusColor(history.status) }}
                >
                  {history.status.toUpperCase()}
                </span>
              </div>
              <div className="history-details">
                <div className="detail">
                  <span className="label">Executed:</span>
                  <span className="value">{new Date(history.executed_at).toLocaleString()}</span>
                </div>
                <div className="detail">
                  <span className="label">Duration:</span>
                  <span className="value">{history.duration_seconds}s</span>
                </div>
                <div className="detail">
                  <span className="label">Actual Savings:</span>
                  <span className="value">${history.actual_savings}</span>
                </div>
              </div>
              {history.status === 'failed' && (
                <div className="error-info">
                  <strong>Error:</strong> {history.error_message}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="empty-state">No execution history available</div>
        )}
      </div>
    </div>
  );

  if (loading) {
    return <div className="loading">Loading ML Optimizer...</div>;
  }

  return (
    <div className="ml-optimizer">
      <div className="header">
        <h1>ML-Powered Optimization & Automation</h1>
        <div className="header-stats">
          <div className="stat">
            <span className="stat-label">Queued Actions</span>
            <span className="stat-value">{filteredActions.length}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Scheduled</span>
            <span className="stat-value">{scheduledActions.length}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Success Rate</span>
            <span className="stat-value">
              {executionHistory.length > 0
                ? ((executionHistory.filter((h) => h.status === 'completed').length / executionHistory.length) * 100).toFixed(0)
                : 0}
              %
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'queue' ? 'active' : ''}`}
          onClick={() => setActiveTab('queue')}
        >
          Action Queue
        </button>
        <button
          className={`tab ${activeTab === 'schedule' ? 'active' : ''}`}
          onClick={() => setActiveTab('schedule')}
        >
          Schedule
        </button>
        <button
          className={`tab ${activeTab === 'impact' ? 'active' : ''}`}
          onClick={() => setActiveTab('impact')}
        >
          Impact
        </button>
        <button
          className={`tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          History
        </button>
      </div>

      {/* Content */}
      <div className="tab-content">
        {activeTab === 'queue' && <ActionQueueView />}
        {activeTab === 'schedule' && <SchedulerView />}
        {activeTab === 'impact' && <ImpactDashboardView />}
        {activeTab === 'history' && <HistoryView />}
      </div>

      {/* Schedule Modal */}
      {showScheduleModal && (
        <div className="modal-overlay" onClick={() => setShowScheduleModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Schedule Action</h2>
              <button className="close-btn" onClick={() => setShowScheduleModal(false)}>×</button>
            </div>
            <div className="modal-content">
              <div className="form-group">
                <label>Date</label>
                <input
                  type="date"
                  value={scheduleData.date}
                  onChange={(e) => setScheduleData({ ...scheduleData, date: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Time</label>
                <input
                  type="time"
                  value={scheduleData.time}
                  onChange={(e) => setScheduleData({ ...scheduleData, time: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={scheduleData.description}
                  onChange={(e) => setScheduleData({ ...scheduleData, description: e.target.value })}
                  placeholder="Add scheduling notes..."
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn cancel" onClick={() => setShowScheduleModal(false)}>
                Cancel
              </button>
              <button className="btn confirm" onClick={confirmSchedule}>
                Schedule Action
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MLOptimizer;
