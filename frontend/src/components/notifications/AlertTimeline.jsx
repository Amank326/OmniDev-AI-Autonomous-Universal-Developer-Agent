import React, { useState, useEffect, useCallback } from 'react';

const AlertTimeline = () => {
  const [alerts, setAlerts] = useState([]);
  const [filteredAlerts, setFilteredAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [timeRange, setTimeRange] = useState(24);

  useEffect(() => {
    fetchAlertTimeline();
    const interval = setInterval(fetchAlertTimeline, 10000);
    return () => clearInterval(interval);
  }, [timeRange]);

  const fetchAlertTimeline = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/notification/alerts/timeline?user_id=current&hours=${timeRange}`);
      const data = await response.json();
      setAlerts(data.data || []);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  // Apply filters
  useEffect(() => {
    let filtered = alerts;

    if (filterSeverity !== 'all') {
      filtered = filtered.filter(a => a.severity === filterSeverity);
    }

    if (filterStatus !== 'all') {
      filtered = filtered.filter(a => a.status === filterStatus);
    }

    setFilteredAlerts(filtered);
  }, [alerts, filterSeverity, filterStatus]);

  const handleAcknowledge = async (alertId) => {
    try {
      await fetch(`/api/v1/notification/alerts/${alertId}/acknowledge`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'current' })
      });
      fetchAlertTimeline();
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const handleResolve = async (alertId) => {
    try {
      await fetch(`/api/v1/notification/alerts/${alertId}/resolve`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' }
      });
      fetchAlertTimeline();
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      'info': { bg: '#dbeafe', text: '#0369a1', icon: 'ℹ️' },
      'warning': { bg: '#fef3c7', text: '#92400e', icon: '⚠️' },
      'critical': { bg: '#fee2e2', text: '#991b1b', icon: '🔴' },
      'urgent': { bg: '#fecaca', text: '#7c2d12', icon: '🚨' }
    };
    return colors[severity] || colors.info;
  };

  const getStatusColor = (status) => {
    const colors = {
      'active': { bg: '#dcfce7', text: '#166534' },
      'resolved': { bg: '#e0e7ff', text: '#3730a3' },
      'acknowledged': { bg: '#dbeafe', text: '#0369a1' },
      'escalated': { bg: '#fecaca', text: '#7c2d12' }
    };
    return colors[status] || colors.active;
  };

  const severities = ['all', 'info', 'warning', 'critical', 'urgent'];
  const statuses = ['all', 'active', 'acknowledged', 'resolved', 'escalated'];

  const activeAlerts = alerts.filter(a => a.status === 'active');
  const resolvedAlerts = alerts.filter(a => a.status === 'resolved');
  const escalatedAlerts = alerts.filter(a => a.status === 'escalated');

  return (
    <div style={{ backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{
        backgroundColor: 'white',
        padding: '20px',
        borderBottom: '1px solid #e0e0e0',
        sticky: 'top',
        zIndex: 100
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto'
        }}>
          <h1 style={{ margin: '0 0 20px 0', fontSize: '24px', fontWeight: 'bold' }}>
            Alert Timeline
          </h1>

          {/* Stats */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            gap: '12px',
            marginBottom: '20px'
          }}>
            <div style={{
              padding: '16px',
              backgroundColor: '#fee2e2',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#991b1b' }}>
                {activeAlerts.length}
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>Active</div>
            </div>

            <div style={{
              padding: '16px',
              backgroundColor: '#fecaca',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#7c2d12' }}>
                {escalatedAlerts.length}
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>Escalated</div>
            </div>

            <div style={{
              padding: '16px',
              backgroundColor: '#dbeafe',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#0369a1' }}>
                {alerts.filter(a => a.status === 'acknowledged').length}
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>Acknowledged</div>
            </div>

            <div style={{
              padding: '16px',
              backgroundColor: '#e0e7ff',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#3730a3' }}>
                {resolvedAlerts.length}
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>Resolved</div>
            </div>
          </div>

          {/* Filters */}
          <div style={{
            display: 'flex',
            gap: '16px',
            alignItems: 'center',
            flexWrap: 'wrap'
          }}>
            <div>
              <label style={{ fontSize: '12px', fontWeight: 'bold', marginRight: '8px' }}>
                Time Range:
              </label>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(parseInt(e.target.value))}
                style={{
                  padding: '6px 10px',
                  border: '1px solid #e0e0e0',
                  borderRadius: '4px',
                  fontSize: '12px'
                }}
              >
                <option value={1}>Last Hour</option>
                <option value={6}>Last 6 Hours</option>
                <option value={24}>Last 24 Hours</option>
                <option value={168}>Last Week</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 'bold', marginRight: '8px' }}>
                Severity:
              </label>
              <select
                value={filterSeverity}
                onChange={(e) => setFilterSeverity(e.target.value)}
                style={{
                  padding: '6px 10px',
                  border: '1px solid #e0e0e0',
                  borderRadius: '4px',
                  fontSize: '12px'
                }}
              >
                {severities.map(sev => (
                  <option key={sev} value={sev}>
                    {sev.charAt(0).toUpperCase() + sev.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 'bold', marginRight: '8px' }}>
                Status:
              </label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                style={{
                  padding: '6px 10px',
                  border: '1px solid #e0e0e0',
                  borderRadius: '4px',
                  fontSize: '12px'
                }}
              >
                {statuses.map(status => (
                  <option key={status} value={status}>
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Timeline Content */}
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '20px'
      }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            Loading timeline...
          </div>
        ) : filteredAlerts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
            No alerts found for the selected filters
          </div>
        ) : (
          <div style={{
            position: 'relative',
            paddingLeft: '40px'
          }}>
            {/* Timeline line */}
            <div style={{
              position: 'absolute',
              left: '16px',
              top: 0,
              bottom: 0,
              width: '2px',
              backgroundColor: '#e0e0e0'
            }} />

            {/* Timeline items */}
            {filteredAlerts.map((alert, index) => {
              const severityColor = getSeverityColor(alert.severity);
              const statusColor = getStatusColor(alert.status);

              return (
                <div key={alert.id} style={{
                  marginBottom: '20px',
                  position: 'relative'
                }}>
                  {/* Timeline dot */}
                  <div style={{
                    position: 'absolute',
                    left: '-27px',
                    top: '8px',
                    width: '20px',
                    height: '20px',
                    borderRadius: '50%',
                    backgroundColor: severityColor.bg,
                    border: `2px solid ${severityColor.text}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '10px',
                    fontWeight: 'bold'
                  }}>
                    {severityColor.icon[0]}
                  </div>

                  {/* Card */}
                  <div
                    onClick={() => setSelectedAlert(selectedAlert?.id === alert.id ? null : alert)}
                    style={{
                      backgroundColor: 'white',
                      padding: '16px',
                      borderRadius: '8px',
                      borderLeft: `4px solid ${severityColor.text}`,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      boxShadow: selectedAlert?.id === alert.id ? '0 4px 12px rgba(0,0,0,0.1)' : 'none'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '8px' }}>
                      <h3 style={{
                        margin: 0,
                        fontSize: '14px',
                        fontWeight: 'bold',
                        flex: 1
                      }}>
                        {alert.title}
                      </h3>
                      <span style={{
                        padding: '2px 8px',
                        backgroundColor: statusColor.bg,
                        color: statusColor.text,
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 'bold',
                        whiteSpace: 'nowrap'
                      }}>
                        {alert.status.toUpperCase()}
                      </span>
                    </div>

                    <div style={{
                      display: 'flex',
                      gap: '12px',
                      marginBottom: '8px',
                      fontSize: '12px'
                    }}>
                      <span style={{
                        backgroundColor: severityColor.bg,
                        color: severityColor.text,
                        padding: '2px 8px',
                        borderRadius: '4px'
                      }}>
                        {alert.severity.toUpperCase()}
                      </span>
                      <span style={{ color: '#999' }}>
                        {new Date(alert.created_at).toLocaleString()}
                      </span>
                    </div>

                    {/* Expanded view */}
                    {selectedAlert?.id === alert.id && (
                      <div style={{
                        marginTop: '12px',
                        paddingTop: '12px',
                        borderTop: '1px solid #e0e0e0'
                      }}>
                        <p style={{
                          margin: '0 0 12px 0',
                          fontSize: '13px',
                          lineHeight: '1.5'
                        }}>
                          {alert.message || 'No additional details'}
                        </p>

                        {alert.status === 'active' && (
                          <div style={{
                            display: 'flex',
                            gap: '8px'
                          }}>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleAcknowledge(alert.id);
                              }}
                              style={{
                                padding: '6px 12px',
                                backgroundColor: '#2563eb',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '12px',
                                fontWeight: 'bold'
                              }}
                            >
                              Acknowledge
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleResolve(alert.id);
                              }}
                              style={{
                                padding: '6px 12px',
                                backgroundColor: '#10b981',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '12px',
                                fontWeight: 'bold'
                              }}
                            >
                              Resolve
                            </button>
                          </div>
                        )}

                        {alert.status !== 'active' && alert.status !== 'resolved' && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleResolve(alert.id);
                            }}
                            style={{
                              padding: '6px 12px',
                              backgroundColor: '#10b981',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '12px',
                              fontWeight: 'bold'
                            }}
                          >
                            Mark as Resolved
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertTimeline;
