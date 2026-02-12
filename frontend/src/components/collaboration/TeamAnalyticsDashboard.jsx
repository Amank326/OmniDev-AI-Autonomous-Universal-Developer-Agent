/**
 * Phase 26: Team Analytics Dashboard Component
 * Team performance metrics, leaderboards, health scoring visualization
 */

import React, { useState, useEffect, useCallback } from 'react';

const TeamAnalyticsDashboard = ({ workspaceId, apiBaseUrl = 'http://localhost:5000' }) => {
  // Data state
  const [teamMetrics, setTeamMetrics] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [teamHealth, setTeamHealth] = useState(null);
  const [memberStats, setMemberStats] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // UI state
  const [activeTab, setActiveTab] = useState('health');
  const [selectedMetric, setSelectedMetric] = useState('productivity');
  const [timeRange, setTimeRange] = useState('week');
  const [sortBy, setSortBy] = useState('score');


  // ========================================================================
  // LIFECYCLE
  // ========================================================================

  useEffect(() => {
    loadTeamMetrics();
    loadTeamHealth();
    loadLeaderboard();
    loadMemberStats();
  }, [workspaceId]);


  // ========================================================================
  // DATA LOADING
  // ========================================================================

  const loadTeamMetrics = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}/team/metrics`
      );
      const data = await response.json();
      setTeamMetrics(data);
    } catch (error) {
      console.error('Failed to load team metrics:', error);
    } finally {
      setLoading(false);
    }
  }, [workspaceId, apiBaseUrl]);

  const loadTeamHealth = useCallback(async () => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}/team/health`
      );
      const data = await response.json();
      setTeamHealth(data);
    } catch (error) {
      console.error('Failed to load team health:', error);
    }
  }, [workspaceId, apiBaseUrl]);

  const loadLeaderboard = useCallback(async () => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}/team/leaderboard`
      );
      const data = await response.json();
      setLeaderboard(data.leaderboard || []);
    } catch (error) {
      console.error('Failed to load leaderboard:', error);
    }
  }, [workspaceId, apiBaseUrl]);

  const loadMemberStats = useCallback(async () => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}/team/metrics`
      );
      const data = await response.json();
      setMemberStats(data.member_stats || []);
    } catch (error) {
      console.error('Failed to load member stats:', error);
    }
  }, [workspaceId, apiBaseUrl]);


  // ========================================================================
  // FORMATTING & CALCULATIONS
  // ========================================================================

  const getHealthColor = (score) => {
    if (score >= 80) return '#2ecc71'; // Green
    if (score >= 60) return '#f39c12'; // Orange
    return '#e74c3c'; // Red
  };

  const getHealthTrend = (trend) => {
    if (trend === 'improving') return '📈';
    if (trend === 'declining') return '📉';
    return '→';
  };

  const getContributionIcon = (type) => {
    const icons = {
      metric_created: '📊',
      insight_generated: '💡',
      forecast_generated: '🔮',
      anomaly_detected: '⚠️',
      dashboard_shared: '📈'
    };
    return icons[type] || '•';
  };

  const formatMetricValue = (value) => {
    if (typeof value === 'number') {
      return value.toFixed(2);
    }
    return value;
  };


  // ========================================================================
  // RENDER: HEALTH SCORE SECTION
  // ========================================================================

  const renderHealthScore = () => {
    if (!teamHealth) return null;

    const { overall_score, engagement, productivity, collaboration, trend } = teamHealth;

    return (
      <div style={{ marginBottom: '30px' }}>
        <h2 style={{ marginTop: 0 }}>Team Health Score</h2>
        
        {/* Overall Score */}
        <div style={{
          padding: '20px',
          backgroundColor: 'white',
          borderRadius: '8px',
          marginBottom: '20px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>
                Overall Health Score
              </div>
              <div style={{
                fontSize: '48px',
                fontWeight: 'bold',
                color: getHealthColor(overall_score)
              }}>
                {overall_score}
              </div>
              <div style={{ fontSize: '12px', color: '#999', marginTop: '5px' }}>
                {getHealthTrend(trend)} {trend}
              </div>
            </div>

            {/* Donut Chart Simulation */}
            <div style={{
              width: '150px',
              height: '150px',
              borderRadius: '50%',
              background: `conic-gradient(
                #3498db 0% ${engagement}%,
                #e74c3c ${engagement}% ${engagement + productivity}%,
                #2ecc71 ${engagement + productivity}% 100%
              )`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 'bold'
            }}>
              <div style={{
                width: '130px',
                height: '130px',
                borderRadius: '50%',
                backgroundColor: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#666'
              }}>
                Health
              </div>
            </div>
          </div>
        </div>

        {/* Component Scores */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '15px' }}>
          {[
            { label: 'Engagement', value: engagement, color: '#3498db' },
            { label: 'Productivity', value: productivity, color: '#e74c3c' },
            { label: 'Collaboration', value: collaboration, color: '#2ecc71' }
          ].map(component => (
            <div
              key={component.label}
              style={{
                padding: '15px',
                backgroundColor: 'white',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
              }}
            >
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
                {component.label}
              </div>
              <div style={{
                fontSize: '24px',
                fontWeight: 'bold',
                color: component.color,
                marginBottom: '10px'
              }}>
                {component.value}%
              </div>
              <div style={{
                height: '6px',
                backgroundColor: '#eee',
                borderRadius: '3px',
                overflow: 'hidden'
              }}>
                <div style={{
                  height: '100%',
                  width: `${component.value}%`,
                  backgroundColor: component.color,
                  transition: 'width 0.3s'
                }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };


  // ========================================================================
  // RENDER: LEADERBOARD SECTION
  // ========================================================================

  const renderLeaderboard = () => {
    return (
      <div style={{ marginBottom: '30px' }}>
        <h2 style={{ marginTop: 0 }}>Top Contributors</h2>
        
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          overflow: 'hidden',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <table style={{
            width: '100%',
            borderCollapse: 'collapse'
          }}>
            <thead>
              <tr style={{ backgroundColor: '#f8f9fa', borderBottom: '2px solid #ddd' }}>
                <th style={{ padding: '15px', textAlign: 'left', fontWeight: '600' }}>Rank</th>
                <th style={{ padding: '15px', textAlign: 'left', fontWeight: '600' }}>Member</th>
                <th style={{ padding: '15px', textAlign: 'center', fontWeight: '600' }}>Productivity</th>
                <th style={{ padding: '15px', textAlign: 'center', fontWeight: '600' }}>Contributions</th>
                <th style={{ padding: '15px', textAlign: 'center', fontWeight: '600' }}>Percentile</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.slice(0, 10).map((member, idx) => (
                <tr
                  key={member.user_id}
                  style={{
                    borderBottom: '1px solid #eee',
                    backgroundColor: idx % 2 === 0 ? '#fff' : '#f9f9f9'
                  }}
                >
                  <td style={{ padding: '15px' }}>
                    <div style={{
                      width: '30px',
                      height: '30px',
                      backgroundColor: idx < 3 ? '#f39c12' : '#bdc3c7',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontWeight: 'bold',
                      fontSize: '12px'
                    }}>
                      {idx + 1}
                    </div>
                  </td>
                  <td style={{ padding: '15px' }}>
                    <div style={{ fontWeight: '500' }}>{member.user_id}</div>
                    <div style={{ fontSize: '12px', color: '#999' }}>
                      {member.role || 'analyst'}
                    </div>
                  </td>
                  <td style={{ padding: '15px', textAlign: 'center' }}>
                    <div style={{
                      display: 'inline-block',
                      padding: '4px 12px',
                      backgroundColor: '#e8f4f8',
                      borderRadius: '4px',
                      fontSize: '14px',
                      fontWeight: '600',
                      color: '#3498db'
                    }}>
                      {member.productivity_score || 75}
                    </div>
                  </td>
                  <td style={{ padding: '15px', textAlign: 'center' }}>
                    <div style={{ fontSize: '14px' }}>{member.total_contributions || 12}</div>
                  </td>
                  <td style={{ padding: '15px', textAlign: 'center' }}>
                    <div style={{
                      display: 'inline-block',
                      padding: '4px 12px',
                      backgroundColor: '#f0f0f0',
                      borderRadius: '4px',
                      fontSize: '12px',
                      color: '#666'
                    }}>
                      {member.percentile || 85}%
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };


  // ========================================================================
  // RENDER: METRICS SECTION
  // ========================================================================

  const renderMetrics = () => {
    if (!teamMetrics) return null;

    const metrics = [
      { key: 'insights_per_day', label: 'Insights/Day', value: teamMetrics.insights_per_day, icon: '💡' },
      { key: 'metrics_created', label: 'Metrics Created', value: teamMetrics.metrics_created, icon: '📊' },
      { key: 'forecast_accuracy', label: 'Forecast Accuracy', value: teamMetrics.forecast_accuracy, icon: '🎯' },
      { key: 'active_members', label: 'Active Members', value: teamMetrics.active_members, icon: '👥' }
    ];

    return (
      <div>
        <h2>Team Metrics</h2>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '15px',
          marginBottom: '30px'
        }}>
          {metrics.map(metric => (
            <div
              key={metric.key}
              style={{
                padding: '20px',
                backgroundColor: 'white',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
              }}
            >
              <div style={{ fontSize: '24px', marginBottom: '8px' }}>{metric.icon}</div>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                {metric.label}
              </div>
              <div style{{
                fontSize: '28px',
                fontWeight: 'bold',
                color: '#2c3e50'
              }}>
                {formatMetricValue(metric.value)}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };


  // ========================================================================
  // RENDER: MEMBER CONTRIBUTIONS
  // ========================================================================

  const renderMemberContributions = () => {
    return (
      <div>
        <h2>Member Contributions</h2>
        
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '20px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '15px' }}>
            {memberStats.slice(0, 8).map(member => (
              <div
                key={member.user_id}
                style={{
                  padding: '15px',
                  backgroundColor: '#f9f9f9',
                  borderRadius: '6px',
                  borderLeft: '4px solid #3498db'
                }}
              >
                <div style={{ fontWeight: '600', marginBottom: '10px' }}>
                  {member.user_id}
                </div>
                
                {/* Contribution Breakdown */}
                <div style={{ fontSize: '12px' }}>
                  {member.contributions && (
                    <div>
                      {Object.entries(member.contributions).map(([type, count]) => (
                        <div
                          key={type}
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            padding: '3px 0',
                            color: '#666'
                          }}
                        >
                          <span>{getContributionIcon(type)} {type}</span>
                          <span style={{ fontWeight: '600' }}>{count}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Productivity Score */}
                <div style={{
                  marginTop: '10px',
                  paddingTop: '10px',
                  borderTop: '1px solid #ddd'
                }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '12px',
                    color: '#666'
                  }}>
                    <span>Score</span>
                    <span style={{ fontWeight: '600', color: '#3498db' }}>
                      {member.productivity_score || 0}/100
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };


  // ========================================================================
  // MAIN RENDER
  // ========================================================================

  return (
    <div style={{
      padding: '20px',
      backgroundColor: '#ecf0f1',
      minHeight: '100vh',
      fontFamily: 'sans-serif'
    }}>
      {/* Header */}
      <div style={{
        marginBottom: '30px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h1 style={{ margin: 0 }}>Team Analytics Dashboard</h1>
        
        {/* Controls */}
        <div style={{ display: 'flex', gap: '10px' }}>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            style={{
              padding: '8px 12px',
              borderRadius: '4px',
              border: '1px solid #bdc3c7',
              backgroundColor: 'white'
            }}
          >
            <option>day</option>
            <option>week</option>
            <option>month</option>
          </select>
        </div>
      </div>

      {/* Content */}
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {renderHealthScore()}
        {renderMetrics()}
        {renderLeaderboard()}
        {renderMemberContributions()}
      </div>

      {/* Loading State */}
      {loading && (
        <div style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          padding: '20px',
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
        }}>
          Loading...
        </div>
      )}
    </div>
  );
};

export default TeamAnalyticsDashboard;
