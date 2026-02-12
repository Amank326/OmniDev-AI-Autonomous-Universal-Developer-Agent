import React, { useState, useEffect } from 'react';

const NotificationPreferences = () => {
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('channels');
  const [dndTime, setDndTime] = useState({ start: '22:00', end: '08:00' });
  const [showMessage, setShowMessage] = useState(false);

  useEffect(() => {
    fetchPreferences();
  }, []);

  const fetchPreferences = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/notification/preferences?user_id=current');
      const data = await response.json();
      setPreferences(data.data || {});
      if (data.data?.dnd) {
        setDndTime({
          start: data.data.dnd.start_time?.slice(0, 5) || '22:00',
          end: data.data.dnd.end_time?.slice(0, 5) || '08:00'
        });
      }
    } catch (error) {
      console.error('Failed to fetch preferences:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateChannelPreference = async (channel, updates) => {
    try {
      await fetch(`/api/v1/notification/preferences/channels/${channel}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'current',
          ...updates
        })
      });
      fetchPreferences();
      setShowMessage(true);
      setTimeout(() => setShowMessage(false), 3000);
    } catch (error) {
      console.error('Failed to update preference:', error);
    }
  };

  const updateDNDSchedule = async () => {
    try {
      await fetch('/api/v1/notification/preferences/dnd', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'current',
          start_time: dndTime.start,
          end_time: dndTime.end,
          allow_urgent: true
        })
      });
      fetchPreferences();
      setShowMessage(true);
      setTimeout(() => setShowMessage(false), 3000);
    } catch (error) {
      console.error('Failed to update DND schedule:', error);
    }
  };

  const toggleGlobalEnable = async (enabled) => {
    try {
      await fetch('/api/v1/notification/preferences/enable-global', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'current',
          enabled
        })
      });
      fetchPreferences();
    } catch (error) {
      console.error('Failed to toggle notifications:', error);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <div style={{ fontSize: '16px', color: '#666' }}>Loading preferences...</div>
      </div>
    );
  }

  const severities = ['info', 'warning', 'critical', 'urgent'];

  return (
    <div style={{ backgroundColor: '#f5f5f5', minHeight: '100vh', padding: '20px' }}>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{
          backgroundColor: 'white',
          padding: '24px',
          borderRadius: '8px',
          marginBottom: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 'bold' }}>
            Notification Preferences
          </h1>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer',
            fontSize: '14px'
          }}>
            <input
              type="checkbox"
              checked={preferences?.globally_enabled || false}
              onChange={(e) => toggleGlobalEnable(e.target.checked)}
            />
            <span>Enable Notifications</span>
          </label>
        </div>

        {/* Success Message */}
        {showMessage && (
          <div style={{
            backgroundColor: '#dcfce7',
            color: '#166534',
            padding: '12px 16px',
            borderRadius: '6px',
            marginBottom: '20px',
            fontSize: '14px'
          }}>
            ✓ Settings saved successfully
          </div>
        )}

        {/* Tabs */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          overflow: 'hidden',
          marginBottom: '20px'
        }}>
          {/* Tab Navigation */}
          <div style={{
            display: 'flex',
            borderBottom: '1px solid #e0e0e0'
          }}>
            {['channels', 'dnd', 'frequency', 'keywords'].map(tab => (
              <button key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  flex: 1,
                  padding: '16px',
                  border: 'none',
                  backgroundColor: activeTab === tab ? '#f5f5f5' : 'white',
                  borderBottom: activeTab === tab ? '3px solid #2563eb' : 'none',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: activeTab === tab ? 'bold' : 'normal',
                  textTransform: 'capitalize'
                }}
              >
                {tab === 'dnd' ? 'Do Not Disturb' : tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div style={{ padding: '24px' }}>
            {/* Channels Tab */}
            {activeTab === 'channels' && (
              <div>
                <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 'bold' }}>
                  Notification Channels
                </h2>
                <p style={{ color: '#666', marginBottom: '20px', fontSize: '14px' }}>
                  Choose which channels you'd like to receive notifications on
                </p>

                {['email', 'sms', 'push', 'in_app'].map((channel, index) => {
                  const pref = preferences?.channels?.[channel] || {};
                  return (
                    <div key={channel} style={{
                      padding: '16px',
                      backgroundColor: pref.enabled ? '#f0f7ff' : '#f5f5f5',
                      borderRadius: '8px',
                      marginBottom: '12px'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
                        <div>
                          <h3 style={{
                            margin: '0 0 4px 0',
                            fontSize: '14px',
                            fontWeight: 'bold',
                            textTransform: 'capitalize'
                          }}>
                            {channel === 'in_app' ? 'In-App' : channel.charAt(0).toUpperCase() + channel.slice(1)}
                          </h3>
                          <p style={{
                            margin: 0,
                            fontSize: '12px',
                            color: '#666'
                          }}>
                            {channel === 'email' && 'Receive notifications via email'}
                            {channel === 'sms' && 'Receive notifications via text message'}
                            {channel === 'push' && 'Receive push notifications on your device'}
                            {channel === 'in_app' && 'See notifications in the app'}
                          </p>
                        </div>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={pref.enabled || false}
                            onChange={(e) => updateChannelPreference(channel, { enabled: e.target.checked })}
                          />
                          <span style={{ fontSize: '12px', fontWeight: 'bold' }}>
                            {pref.enabled ? 'Enabled' : 'Disabled'}
                          </span>
                        </label>
                      </div>

                      {pref.enabled && (
                        <div style={{
                          paddingTop: '12px',
                          borderTop: '1px solid #e0e0e0'
                        }}>
                          <div style={{ marginBottom: '12px' }}>
                            <label style={{
                              fontSize: '12px',
                              fontWeight: 'bold',
                              display: 'block',
                              marginBottom: '4px'
                            }}>
                              Minimum Severity
                            </label>
                            <select
                              value={pref.min_severity || 'info'}
                              onChange={(e) => updateChannelPreference(channel, { min_severity: e.target.value })}
                              style={{
                                padding: '6px 10px',
                                border: '1px solid #e0e0e0',
                                borderRadius: '4px',
                                fontSize: '12px'
                              }}
                            >
                              {severities.map(sev => (
                                <option key={sev} value={sev}>
                                  {sev.charAt(0).toUpperCase() + sev.slice(1)}+
                                </option>
                              ))}
                            </select>
                          </div>

                          <div>
                            <label style={{
                              fontSize: '12px',
                              fontWeight: 'bold',
                              display: 'block',
                              marginBottom: '4px'
                            }}>
                              Max per hour: {pref.frequency_cap || 'Unlimited'}
                            </label>
                            <input
                              type="range"
                              min="0"
                              max="50"
                              value={pref.frequency_cap || 50}
                              onChange={(e) => updateChannelPreference(channel, { frequency_cap: parseInt(e.target.value) })}
                              style={{ width: '100%' }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* DND Tab */}
            {activeTab === 'dnd' && (
              <div>
                <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 'bold' }}>
                  Do Not Disturb Schedule
                </h2>
                <p style={{ color: '#666', marginBottom: '20px', fontSize: '14px' }}>
                  Set a time window when you don't want to be interrupted. Urgent alerts may still come through.
                </p>

                <div style={{
                  padding: '20px',
                  backgroundColor: '#f5f5f5',
                  borderRadius: '8px'
                }}>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '20px',
                    marginBottom: '20px'
                  }}>
                    <div>
                      <label style={{
                        fontSize: '12px',
                        fontWeight: 'bold',
                        display: 'block',
                        marginBottom: '8px'
                      }}>
                        Start Time
                      </label>
                      <input
                        type="time"
                        value={dndTime.start}
                        onChange={(e) => setDndTime(prev => ({ ...prev, start: e.target.value }))}
                        style={{
                          width: '100%',
                          padding: '10px',
                          border: '1px solid #e0e0e0',
                          borderRadius: '6px',
                          fontSize: '14px',
                          boxSizing: 'border-box'
                        }}
                      />
                    </div>
                    <div>
                      <label style={{
                        fontSize: '12px',
                        fontWeight: 'bold',
                        display: 'block',
                        marginBottom: '8px'
                      }}>
                        End Time
                      </label>
                      <input
                        type="time"
                        value={dndTime.end}
                        onChange={(e) => setDndTime(prev => ({ ...prev, end: e.target.value }))}
                        style={{
                          width: '100%',
                          padding: '10px',
                          border: '1px solid #e0e0e0',
                          borderRadius: '6px',
                          fontSize: '14px',
                          boxSizing: 'border-box'
                        }}
                      />
                    </div>
                  </div>

                  <div style={{
                    padding: '12px',
                    backgroundColor: '#fef3c7',
                    borderRadius: '6px',
                    marginBottom: '12px',
                    fontSize: '12px',
                    color: '#92400e'
                  }}>
                    ⚠️ Urgent alerts will still be delivered during DND
                  </div>

                  <button
                    onClick={updateDNDSchedule}
                    style={{
                      padding: '10px 20px',
                      backgroundColor: '#2563eb',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '14px',
                      fontWeight: 'bold'
                    }}
                  >
                    Save Schedule
                  </button>
                </div>
              </div>
            )}

            {/* Frequency Tab */}
            {activeTab === 'frequency' && (
              <div>
                <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 'bold' }}>
                  Notification Frequency
                </h2>
                <p style={{ color: '#666', marginBottom: '20px', fontSize: '14px' }}>
                  Control how often you receive notifications
                </p>

                <div style={{
                  padding: '20px',
                  backgroundColor: '#f5f5f5',
                  borderRadius: '8px'
                }}>
                  <div style={{ marginBottom: '20px' }}>
                    <label style={{
                      fontSize: '12px',
                      fontWeight: 'bold',
                      display: 'block',
                      marginBottom: '8px'
                    }}>
                      Maximum Daily Notifications: {preferences?.max_daily_notifications || 'Unlimited'}
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={preferences?.max_daily_notifications || 100}
                      onChange={(e) => {
                        // Handle change
                      }}
                      style={{ width: '100%' }}
                    />
                    <div style={{
                      fontSize: '12px',
                      color: '#666',
                      marginTop: '4px'
                    }}>
                      Set to 0 for unlimited
                    </div>
                  </div>

                  <div style={{
                    padding: '12px',
                    backgroundColor: '#dbeafe',
                    borderRadius: '6px',
                    fontSize: '12px',
                    color: '#1e40af'
                  }}>
                    ℹ️ Frequency caps per channel can be set in the Channels tab
                  </div>
                </div>
              </div>
            )}

            {/* Keywords Tab */}
            {activeTab === 'keywords' && (
              <div>
                <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 'bold' }}>
                  Keywords & Muting
                </h2>
                <p style={{ color: '#666', marginBottom: '20px', fontSize: '14px' }}>
                  Add keywords to follow or mute specific notifications
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                  {/* Keywords to Follow */}
                  <div style={{
                    padding: '16px',
                    backgroundColor: '#f0f7ff',
                    borderRadius: '8px'
                  }}>
                    <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: 'bold' }}>
                      📌 Keywords to Follow
                    </h3>
                    <p style={{ margin: '0 0 12px 0', fontSize: '12px', color: '#666' }}>
                      Get notified for specific keywords
                    </p>
                    <div style={{
                      display: 'flex',
                      gap: '8px',
                      marginBottom: '12px'
                    }}>
                      <input
                        type="text"
                        placeholder="Add keyword..."
                        style={{
                          flex: 1,
                          padding: '8px 12px',
                          border: '1px solid #e0e0e0',
                          borderRadius: '4px',
                          fontSize: '12px'
                        }}
                      />
                      <button style={{
                        padding: '8px 12px',
                        backgroundColor: '#2563eb',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}>
                        Add
                      </button>
                    </div>
                    <div>
                      {preferences?.keywords_to_follow?.map(keyword => (
                        <div key={keyword} style={{
                          padding: '6px 8px',
                          backgroundColor: 'white',
                          borderRadius: '4px',
                          marginBottom: '4px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          fontSize: '12px'
                        }}>
                          <span>{keyword}</span>
                          <button style={{
                            background: 'none',
                            border: 'none',
                            color: '#999',
                            cursor: 'pointer'
                          }}>
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Muted Keywords */}
                  <div style={{
                    padding: '16px',
                    backgroundColor: '#fee2e2',
                    borderRadius: '8px'
                  }}>
                    <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: 'bold' }}>
                      🔇 Muted Keywords
                    </h3>
                    <p style={{ margin: '0 0 12px 0', fontSize: '12px', color: '#666' }}>
                      Don't notify me about these keywords
                    </p>
                    <div style={{
                      display: 'flex',
                      gap: '8px',
                      marginBottom: '12px'
                    }}>
                      <input
                        type="text"
                        placeholder="Add keyword to mute..."
                        style={{
                          flex: 1,
                          padding: '8px 12px',
                          border: '1px solid #e0e0e0',
                          borderRadius: '4px',
                          fontSize: '12px'
                        }}
                      />
                      <button style={{
                        padding: '8px 12px',
                        backgroundColor: '#ef4444',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}>
                        Mute
                      </button>
                    </div>
                    <div>
                      {preferences?.muted_keywords?.map(keyword => (
                        <div key={keyword} style={{
                          padding: '6px 8px',
                          backgroundColor: 'white',
                          borderRadius: '4px',
                          marginBottom: '4px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          fontSize: '12px'
                        }}>
                          <span>{keyword}</span>
                          <button style={{
                            background: 'none',
                            border: 'none',
                            color: '#999',
                            cursor: 'pointer'
                          }}>
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationPreferences;
