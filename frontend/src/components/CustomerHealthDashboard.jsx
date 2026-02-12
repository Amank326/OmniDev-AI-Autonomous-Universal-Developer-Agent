/**
 * Customer Health Dashboard Component
 * Real-time health visualization, alerts, and expansion opportunities
 * Uses: success_metrics_service (health), customer_health_dashboard_service (aggregation)
 */

import React, { useState, useEffect } from 'react';
import './CustomerHealthDashboard.css';

const CustomerHealthDashboard = ({ customerId, apiBaseUrl = '/api/v1' }) => {
  // ========================================================================
  // STATE MANAGEMENT
  // ========================================================================

  const [customerHealth, setCustomerHealth] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [csm_actions, setCsmActions] = useState([]);
  const [portfolioMetrics, setPortfolioMetrics] = useState(null);
  const [expandedSection, setExpandedSection] = useState('health');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ========================================================================
  // DATA FETCHING
  // ========================================================================

  useEffect(() => {
    const fetchHealthData = async () => {
      try {
        setLoading(true);
        const headers = { 'Authorization': `Bearer ${localStorage.getItem('token')}` };

        // Fetch customer health
        const healthRes = await fetch(
          `${apiBaseUrl}/success/health/${customerId}`,
          { headers }
        );
        const healthData = await healthRes.json();
        setCustomerHealth(healthData);

        // Fetch alerts
        const alertsRes = await fetch(
          `${apiBaseUrl}/success/alerts/${customerId}`,
          { headers }
        );
        const alertsData = await alertsRes.json();
        setAlerts(alertsData.alerts || []);

        // Fetch CSM actions
        const actionsRes = await fetch(
          `${apiBaseUrl}/success/csm/${customerId}/actions`,
          { headers }
        );
        const actionsData = await actionsRes.json();
        setCsmActions(actionsData.actions || []);

        // Fetch portfolio metrics (for context)
        const portfolioRes = await fetch(
          `${apiBaseUrl}/success/health/distribution/portfolio`,
          { headers }
        );
        const portfolioData = await portfolioRes.json();
        setPortfolioMetrics(portfolioData);

        setError(null);
      } catch (err) {
        setError(err.message);
        console.error('Error fetching health data:', err);
      } finally {
        setLoading(false);
      }
    };

    if (customerId) {
      fetchHealthData();
      // Poll every 5 minutes
      const interval = setInterval(fetchHealthData, 5 * 60 * 1000);
      return () => clearInterval(interval);
    }
  }, [customerId, apiBaseUrl]);

  // ========================================================================
  // RENDERING HELPERS
  // ========================================================================

  const getHealthColor = (score) => {
    if (score >= 80) return 'health-thriving';
    if (score >= 60) return 'health-healthy';
    if (score >= 40) return 'health-at-risk';
    return 'health-critical';
  };

  const getHealthLabel = (score) => {
    if (score >= 80) return 'THRIVING';
    if (score >= 60) return 'HEALTHY';
    if (score >= 40) return 'AT RISK';
    return 'CRITICAL';
  };

  const getAlertIcon = (level) => {
    switch (level) {
      case 'critical': return '🔴';
      case 'high': return '🟠';
      case 'medium': return '🟡';
      default: return '🔵';
    }
  };

  const renderHealthGauge = (score) => {
    const circumference = 2 * Math.PI * 45;
    const offset = circumference - (score / 100) * circumference;

    return (
      <div className="health-gauge">
        <svg width="120" height="120" viewBox="0 0 120 120">
          <circle
            cx="60"
            cy="60"
            r="45"
            className="gauge-background"
          />
          <circle
            cx="60"
            cy="60"
            r="45"
            className={`gauge-fill ${getHealthColor(score)}`}
            style={{
              strokeDasharray: circumference,
              strokeDashoffset: offset,
            }}
          />
          <text x="60" y="60" textAnchor="middle" dominantBaseline="middle" className="gauge-text">
            {score}
          </text>
        </svg>
        <div className="gauge-label">{getHealthLabel(score)}</div>
      </div>
    );
  };

  // ========================================================================
  // MAIN RENDER
  // ========================================================================

  if (loading) return <div className="dashboard-loading">Loading health data...</div>;
  if (error) return <div className="dashboard-error">Error: {error}</div>;
  if (!customerHealth) return <div className="dashboard-error">No health data available</div>;

  const healthScore = customerHealth.overall_score || 0;
  const healthLevel = getHealthLabel(healthScore);
  const components = customerHealth.component_scores || {};

  return (
    <div className="customer-health-dashboard">
      {/* ================================================================ */}
      {/* HEADER WITH HEALTH SUMMARY */}
      {/* ================================================================ */}
      <div className="dashboard-header">
        <h1>Customer Health Dashboard</h1>
        <div className="header-meta">
          <span className="customer-id">{customerId}</span>
          <span className="last-updated">
            Updated: {new Date(customerHealth.last_updated).toLocaleString()}
          </span>
        </div>
      </div>

      {/* ================================================================ */}
      {/* MAIN HEALTH GAUGE */}
      {/* ================================================================ */}
      <div className="health-summary-card">
        <div className="gauge-container">
          {renderHealthGauge(healthScore)}
        </div>

        <div className="health-details">
          <h2>Overall Health: {healthLevel}</h2>
          <p className="health-score">Score: {healthScore}/100</p>

          <div className="health-trend">
            <span className="trend-label">Trend:</span>
            <span className={`trend-badge ${customerHealth.trend}`}>
              {customerHealth.trend.toUpperCase()}
            </span>
          </div>

          <p className="trend-explanation">
            {customerHealth.trend_explanation}
          </p>

          {/* Expansion indicator */}
          {customerHealth.expansion_opportunities > 0 && (
            <div className="expansion-indicator">
              <span className="expansion-icon">💰</span>
              <span className="expansion-text">
                {customerHealth.expansion_opportunities} expansion opportunities identified
              </span>
            </div>
          )}
        </div>
      </div>

      {/* ================================================================ */}
      {/* COMPONENT BREAKDOWN */}
      {/* ================================================================ */}
      <div className="components-section">
        <h3>Health Component Breakdown</h3>
        <div className="components-grid">
          {[
            { key: 'adoption', label: 'Feature Adoption', icon: '📊' },
            { key: 'engagement', label: 'Engagement', icon: '🔥' },
            { key: 'support_sentiment', label: 'Support Sentiment', icon: '😊' },
            { key: 'revenue_trend', label: 'Revenue Trend', icon: '💵' },
            { key: 'nps', label: 'NPS', icon: '⭐' },
          ].map((comp) => {
            const score = components[comp.key] || 0;
            return (
              <div key={comp.key} className="component-card">
                <div className="component-header">
                  <span className="component-icon">{comp.icon}</span>
                  <span className="component-label">{comp.label}</span>
                </div>
                <div className="component-score">
                  <div className="score-bar">
                    <div
                      className={`score-fill ${getHealthColor(score)}`}
                      style={{ width: `${score}%` }}
                    />
                  </div>
                  <span className="score-number">{score}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ================================================================ */}
      {/* KEY DRIVERS & RISK FACTORS */}
      {/* ================================================================ */}
      <div className="insights-section">
        <div className="insights-column drivers-column">
          <h3>✅ Key Success Drivers</h3>
          <div className="insights-list">
            {customerHealth.key_drivers && customerHealth.key_drivers.length > 0 ? (
              customerHealth.key_drivers.map((driver, idx) => (
                <div key={idx} className="insight-item driver-item">
                  <span className="insight-icon">✓</span>
                  <span>{driver}</span>
                </div>
              ))
            ) : (
              <p className="no-items">No key drivers identified</p>
            )}
          </div>
        </div>

        <div className="insights-column risks-column">
          <h3>⚠️ Risk Factors</h3>
          <div className="insights-list">
            {customerHealth.risk_factors && customerHealth.risk_factors.length > 0 ? (
              customerHealth.risk_factors.map((risk, idx) => (
                <div key={idx} className="insight-item risk-item">
                  <span className="insight-icon">!</span>
                  <span>{risk}</span>
                </div>
              ))
            ) : (
              <p className="no-items">No risk factors identified</p>
            )}
          </div>
        </div>
      </div>

      {/* ================================================================ */}
      {/* ALERTS SECTION */}
      {/* ================================================================ */}
      {alerts.length > 0 && (
        <div className="alerts-section">
          <h3>🚨 Active Alerts ({alerts.length})</h3>
          <div className="alerts-list">
            {alerts.map((alert, idx) => (
              <div key={idx} className={`alert-card alert-${alert.level}`}>
                <div className="alert-header">
                  <span className="alert-icon">{getAlertIcon(alert.level)}</span>
                  <span className="alert-title">{alert.title}</span>
                  <span className="alert-level">{alert.level.toUpperCase()}</span>
                </div>
                <p className="alert-description">{alert.description}</p>
                <div className="alert-action">
                  <span className="action-label">Action:</span>
                  <span className="action-required">{alert.action_required}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ================================================================ */}
      {/* CSM ACTIONS SECTION */}
      {/* ================================================================ */}
      {csm_actions.length > 0 && (
        <div className="actions-section">
          <h3>📋 Recommended CSM Actions ({csm_actions.length})</h3>
          <div className="actions-list">
            {csm_actions.map((action, idx) => (
              <div key={idx} className={`action-card action-${action.priority}`}>
                <div className="action-header">
                  <span className="action-type">{action.type.replace(/_/g, ' ').toUpperCase()}</span>
                  <span className="action-priority">{action.priority.toUpperCase()}</span>
                </div>
                <h4>{action.title}</h4>
                <p className="action-desc">{action.description}</p>
                <div className="action-details">
                  <div className="detail-item">
                    <span className="detail-label">Due:</span>
                    <span>{new Date(action.due_date).toLocaleDateString()}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Activity:</span>
                    <span>{action.csm_activity}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ================================================================ */}
      {/* PORTFOLIO CONTEXT */}
      {/* ================================================================ */}
      {portfolioMetrics && (
        <div className="portfolio-context">
          <h3>Portfolio Context</h3>
          <div className="portfolio-stats">
            <div className="stat-item">
              <span className="stat-label">Total Customers</span>
              <span className="stat-value">{portfolioMetrics.total_customers}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Your Health vs Avg</span>
              <span className="stat-value">
                {healthScore} vs {portfolioMetrics.average_score} avg
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">At-Risk %</span>
              <span className="stat-value">{portfolioMetrics.at_risk_percent}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomerHealthDashboard;
