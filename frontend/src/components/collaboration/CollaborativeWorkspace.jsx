/**
 * Phase 26: Collaborative Workspace Component
 * Main workspace with real-time collaboration, presence, and shared tools
 */

import React, { useState, useEffect, useCallback } from 'react';

const CollaborativeWorkspace = ({ workspaceId, userId, apiBaseUrl = 'http://localhost:5000' }) => {
  // Workspace state
  const [workspace, setWorkspace] = useState(null);
  const [members, setMembers] = useState([]);
  const [presence, setPresence] = useState({});
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // UI state
  const [selectedView, setSelectedView] = useState('metrics');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeUsers, setActiveUsers] = useState([]);
  const [showActivityFeed, setShowActivityFeed] = useState(true);
  
  // Collaboration state
  const [typingUsers, setTypingUsers] = useState(new Set());
  const [userCursors, setUserCursors] = useState({});
  const [notifications, setNotifications] = useState([]);
  
  // WebSocket
  const [socket, setSocket] = useState(null);


  // ========================================================================
  // LIFECYCLE
  // ========================================================================

  useEffect(() => {
    loadWorkspace();
    loadMembers();
    initializeWebSocket();
  }, [workspaceId]);

  useEffect(() => {
    if (socket) {
      socket.emit('update_presence', {
        user_id: userId,
        workspace_id: workspaceId,
        status: 'active'
      });
    }
  }, [socket, userId, workspaceId]);


  // ========================================================================
  // INITIALIZATION
  // ========================================================================

  const loadWorkspace = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}`);
      const data = await response.json();
      setWorkspace(data);
    } catch (error) {
      console.error('Failed to load workspace:', error);
    } finally {
      setLoading(false);
    }
  }, [workspaceId, apiBaseUrl]);

  const loadMembers = useCallback(async () => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}/members`
      );
      const data = await response.json();
      setMembers(data.members || []);
    } catch (error) {
      console.error('Failed to load members:', error);
    }
  }, [workspaceId, apiBaseUrl]);

  const initializeWebSocket = useCallback(() => {
    // In real implementation, connect to WebSocket
    // For demo, simulate with events
    const mockSocket = {
      emit: (event, data) => {
        console.log(`WebSocket event: ${event}`, data);
      },
      on: (event, callback) => {
        console.log(`Listening for: ${event}`);
      }
    };
    
    setSocket(mockSocket);
  }, []);


  // ========================================================================
  // WORKSPACE ACTIONS
  // ========================================================================

  const getActiveMembers = useCallback(() => {
    return members.filter(m => presence[m.user_id]?.status === 'active');
  }, [members, presence]);

  const broadcastActivity = useCallback((action, resourceId) => {
    if (socket) {
      socket.emit('stream_activity', {
        user_id: userId,
        workspace_id: workspaceId,
        action: action,
        resource: resourceId
      });
    }
  }, [socket, userId, workspaceId]);

  const handleMetricCreated = useCallback((metricId, metricName) => {
    if (socket) {
      socket.emit('metric_created', {
        workspace_id: workspaceId,
        metric_id: metricId,
        metric_name: metricName,
        created_by: userId
      });
    }
    
    broadcastActivity('created_metric', metricId);
  }, [socket, workspaceId, userId, broadcastActivity]);

  const handleInsightShared = useCallback((insightId) => {
    if (socket) {
      socket.emit('insight_shared', {
        workspace_id: workspaceId,
        insight_id: insightId,
        shared_by: userId,
        visibility: 'team'
      });
    }
    
    broadcastActivity('shared_insight', insightId);
  }, [socket, workspaceId, userId, broadcastActivity]);

  const handleDashboardUpdated = useCallback((dashboardId, changes) => {
    if (socket) {
      socket.emit('dashboard_updated', {
        workspace_id: workspaceId,
        dashboard_id: dashboardId,
        updated_by: userId,
        changes: changes
      });
    }
  }, [socket, workspaceId, userId]);

  const handleUserTyping = useCallback((metricId) => {
    if (socket) {
      socket.emit('user_typing', {
        workspace_id: workspaceId,
        user_id: userId,
        metric_id: metricId
      });
    }
  }, [socket, workspaceId, userId]);

  const handleUserStoppedTyping = useCallback(() => {
    if (socket) {
      socket.emit('stop_typing', {
        workspace_id: workspaceId,
        user_id: userId
      });
    }
  }, [socket, workspaceId, userId]);


  // ========================================================================
  // PRESENCE TRACKING
  // ========================================================================

  const updatePresence = useCallback((status, currentView = null) => {
    if (socket) {
      socket.emit('update_presence', {
        user_id: userId,
        workspace_id: workspaceId,
        status: status,
        current_view: currentView
      });
    }

    setPresence(prev => ({
      ...prev,
      [userId]: {
        status: status,
        current_view: currentView,
        last_activity: new Date().toISOString()
      }
    }));
  }, [socket, userId, workspaceId]);

  const getMemberAvatarColor = (userId) => {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F'];
    return colors[userId.charCodeAt(0) % colors.length];
  };


  // ========================================================================
  // RENDER SIDEBAR
  // ========================================================================

  const renderSidebar = () => {
    return (
      <div style={{
        width: sidebarOpen ? '300px' : '60px',
        backgroundColor: '#2c3e50',
        color: 'white',
        padding: '15px',
        overflowY: 'auto',
        transition: 'width 0.3s',
        boxShadow: '0 0 10px rgba(0,0,0,0.2)'
      }}>
        {/* Collapse Button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          style={{
            background: 'none',
            border: 'none',
            color: 'white',
            cursor: 'pointer',
            marginBottom: '20px'
          }}
        >
          {sidebarOpen ? '←' : '→'}
        </button>

        {sidebarOpen && (
          <>
            {/* Workspace Info */}
            <div style={{ marginBottom: '20px' }}>
              <h3 style={{ margin: '0 0 10px 0', fontSize: '14px' }}>
                {workspace?.name || 'Loading...'}
              </h3>
              <div style={{ fontSize: '12px', color: '#bdc3c7' }}>
                {members.length} members
              </div>
            </div>

            {/* Active Members */}
            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ margin: '0 0 10px 0', fontSize: '12px', color: '#95a5a6' }}>
                ONLINE ({getActiveMembers().length})
              </h4>
              {getActiveMembers().map(member => (
                <div
                  key={member.user_id}
                  style={{
                    padding: '8px',
                    marginBottom: '5px',
                    backgroundColor: 'rgba(255,255,255,0.1)',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  <div style={{
                    width: '8px',
                    height: '8px',
                    backgroundColor: '#2ecc71',
                    borderRadius: '50%'
                  }} />
                  <div style={{ fontSize: '12px', flex: 1 }}>
                    {member.user_id}
                  </div>
                  {typingUsers.has(member.user_id) && (
                    <div style={{ fontSize: '10px', color: '#f39c12' }}>✏️</div>
                  )}
                </div>
              ))}
            </div>

            {/* Navigation */}
            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ margin: '0 0 10px 0', fontSize: '12px', color: '#95a5a6' }}>
                VIEWS
              </h4>
              {['metrics', 'dashboards', 'insights', 'shared'].map(view => (
                <button
                  key={view}
                  onClick={() => {
                    setSelectedView(view);
                    updatePresence('active', view);
                  }}
                  style={{
                    width: '100%',
                    padding: '10px',
                    marginBottom: '5px',
                    backgroundColor: selectedView === view ? '#3498db' : 'transparent',
                    border: 'none',
                    color: 'white',
                    textAlign: 'left',
                    cursor: 'pointer',
                    borderRadius: '4px'
                  }}
                >
                  {view.toUpperCase()}
                </button>
              ))}
            </div>

            {/* Activity Toggle */}
            <button
              onClick={() => setShowActivityFeed(!showActivityFeed)}
              style={{
                width: '100%',
                padding: '10px',
                backgroundColor: '#e74c3c',
                border: 'none',
                color: 'white',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              {showActivityFeed ? 'Hide' : 'Show'} Activity
            </button>
          </>
        )}
      </div>
    );
  };


  // ========================================================================
  // RENDER MAIN CONTENT
  // ========================================================================

  const renderMainContent = () => {
    return (
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <div style={{
          padding: '15px 20px',
          backgroundColor: '#fff',
          borderBottom: '1px solid #ddd',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h2 style={{ margin: 0 }}>{selectedView.toUpperCase()}</h2>
          <div style={{ display: 'flex', gap: '10px' }}>
            <span style={{ fontSize: '12px', color: '#666' }}>
              {getActiveMembers().length} online
            </span>
          </div>
        </div>

        {/* Content Area */}
        <div style={{ flex: 1, padding: '20px', overflowY: 'auto' }}>
          {selectedView === 'metrics' && (
            <div>
              <h3>Metrics</h3>
              <p style={{ color: '#666' }}>
                Collaborative metrics creation and editing
              </p>
              <button
                onClick={() => handleMetricCreated('metric_1', 'Sample Metric')}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#3498db',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Create Metric
              </button>
            </div>
          )}

          {selectedView === 'dashboards' && (
            <div>
              <h3>Dashboards</h3>
              <p style={{ color: '#666' }}>
                Shared dashboard configuration and editing
              </p>
            </div>
          )}

          {selectedView === 'insights' && (
            <div>
              <h3>Insights</h3>
              <p style={{ color: '#666' }}>
                Team insights and recommendations
              </p>
              <button
                onClick={() => handleInsightShared('insight_1')}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#27ae60',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Share Insight
              </button>
            </div>
          )}

          {selectedView === 'shared' && (
            <div>
              <h3>Shared Resources</h3>
              <p style={{ color: '#666' }}>
                Recently shared metrics, dashboards, and insights
              </p>
            </div>
          )}
        </div>
      </div>
    );
  };


  // ========================================================================
  // RENDER ACTIVITY FEED
  // ========================================================================

  const renderActivityFeed = () => {
    return (
      <div style={{
        width: '250px',
        backgroundColor: '#f5f5f5',
        borderLeft: '1px solid #ddd',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{
          padding: '15px',
          borderBottom: '1px solid #ddd',
          fontWeight: 'bold',
          fontSize: '12px'
        }}>
          ACTIVITY FEED
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '10px' }}>
          {[1, 2, 3].map((item) => (
            <div
              key={item}
              style={{
                padding: '10px',
                marginBottom: '10px',
                backgroundColor: 'white',
                borderRadius: '4px',
                fontSize: '12px',
                borderLeft: '3px solid #3498db'
              }}
            >
              <div style={{ fontWeight: 'bold', marginBottom: '3px' }}>
                User created metric
              </div>
              <div style={{ color: '#666', fontSize: '11px' }}>
                2 minutes ago
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };


  // ========================================================================
  // MAIN RENDER
  // ========================================================================

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      backgroundColor: '#ecf0f1',
      fontFamily: 'sans-serif'
    }}>
      {/* Sidebar */}
      {renderSidebar()}

      {/* Main Content */}
      {renderMainContent()}

      {/* Activity Feed */}
      {showActivityFeed && renderActivityFeed()}

      {/* Notifications */}
      {notifications.length > 0 && (
        <div style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          maxWidth: '300px',
          maxHeight: '400px',
          overflowY: 'auto'
        }}>
          {notifications.map((notif, idx) => (
            <div
              key={idx}
              style={{
                padding: '15px',
                backgroundColor: '#fff',
                borderRadius: '4px',
                marginBottom: '10px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                fontSize: '14px'
              }}
            >
              {notif.message}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CollaborativeWorkspace;
