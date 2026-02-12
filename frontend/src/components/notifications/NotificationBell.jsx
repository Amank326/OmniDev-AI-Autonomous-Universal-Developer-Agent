import React, { useState, useEffect, useRef } from 'react';

const NotificationBell = ({ onNotificationClick }) => {
  const [notifications, setNotifications] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 5000);

    // Close dropdown when clicking outside
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      clearInterval(interval);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const fetchNotifications = async () => {
    try {
      const response = await fetch('/api/v1/notification/notifications?user_id=current&limit=10');
      const data = await response.json();
      const notifList = data.data || [];
      setNotifications(notifList);

      const unread = notifList.filter(n => n.status !== 'read').length;
      setUnreadCount(unread);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  const handleMarkAsRead = async (notificationId, e) => {
    e.stopPropagation();
    try {
      await fetch(`/api/v1/notification/notifications/${notificationId}/read`, {
        method: 'PUT'
      });
      fetchNotifications();
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const handleDeleteNotification = async (notificationId, e) => {
    e.stopPropagation();
    try {
      await fetch(`/api/v1/notification/notifications/${notificationId}`, {
        method: 'DELETE'
      });
      fetchNotifications();
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  const getTypeIcon = (type) => {
    const icons = {
      'alert': '🚨',
      'mention': '@️',
      'update': '📢',
      'system': '⚙️',
      'reminder': '🔔',
      'collaboration': '👥'
    };
    return icons[type] || '📬';
  };

  const getTypeColor = (type) => {
    const colors = {
      'alert': '#fee2e2',
      'mention': '#dbeafe',
      'update': '#fef3c7',
      'system': '#f0f0f0',
      'reminder': '#dcfce7',
      'collaboration': '#ddd6fe'
    };
    return colors[type] || '#f5f5f5';
  };

  return (
    <div style={{ position: 'relative' }} ref={dropdownRef}>
      {/* Bell Button */}
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        style={{
          position: 'relative',
          background: 'none',
          border: 'none',
          fontSize: '24px',
          cursor: 'pointer',
          padding: '8px',
          transition: 'transform 0.2s'
        }}
        onMouseEnter={(e) => e.target.style.transform = 'scale(1.1)'}
        onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
      >
        🔔
        
        {/* Badge */}
        {unreadCount > 0 && (
          <div style={{
            position: 'absolute',
            top: '-2px',
            right: '-2px',
            backgroundColor: '#ef4444',
            color: 'white',
            width: '24px',
            height: '24px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '12px',
            fontWeight: 'bold',
            border: '2px solid white'
          }}>
            {unreadCount > 99 ? '99+' : unreadCount}
          </div>
        )}
      </button>

      {/* Dropdown */}
      {showDropdown && (
        <div style={{
          position: 'absolute',
          right: '-20px',
          top: '100%',
          marginTop: '8px',
          width: '400px',
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: '0 10px 40px rgba(0,0,0,0.2)',
          zIndex: 1000,
          maxHeight: '500px',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}>
          {/* Header */}
          <div style={{
            padding: '16px',
            borderBottom: '1px solid #e0e0e0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <h3 style={{
              margin: 0,
              fontSize: '16px',
              fontWeight: 'bold'
            }}>
              Notifications
            </h3>
            <div style={{
              display: 'flex',
              gap: '8px'
            }}>
              <span style={{
                fontSize: '12px',
                backgroundColor: '#f0f0f0',
                padding: '2px 8px',
                borderRadius: '4px',
                color: '#666'
              }}>
                {unreadCount} new
              </span>
            </div>
          </div>

          {/* Notifications List */}
          <div style={{
            overflowY: 'auto',
            flex: 1
          }}>
            {loading ? (
              <div style={{
                padding: '20px',
                textAlign: 'center',
                color: '#999',
                fontSize: '14px'
              }}>
                Loading...
              </div>
            ) : notifications.length === 0 ? (
              <div style={{
                padding: '20px',
                textAlign: 'center',
                color: '#999',
                fontSize: '14px'
              }}>
                No notifications
              </div>
            ) : (
              notifications.map(notification => (
                <div
                  key={notification.id}
                  style={{
                    padding: '12px 16px',
                    borderBottom: '1px solid #f0f0f0',
                    backgroundColor: notification.status === 'read' ? 'white' : '#fafafa',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s',
                    display: 'flex',
                    gap: '12px'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = notification.status === 'read' ? '#f5f5f5' : '#f0f0f0'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = notification.status === 'read' ? 'white' : '#fafafa'}
                >
                  {/* Icon */}
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    backgroundColor: getTypeColor(notification.type),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    fontSize: '16px'
                  }}>
                    {getTypeIcon(notification.type)}
                  </div>

                  {/* Content */}
                  <div style={{
                    flex: 1,
                    minWidth: 0
                  }}>
                    <h4 style={{
                      margin: '0 0 2px 0',
                      fontSize: '13px',
                      fontWeight: notification.status === 'read' ? 'normal' : 'bold',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {notification.title}
                    </h4>
                    <p style={{
                      margin: '0 0 4px 0',
                      fontSize: '12px',
                      color: '#666',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {notification.body}
                    </p>
                    <div style={{
                      fontSize: '11px',
                      color: '#999'
                    }}>
                      {getRelativeTime(new Date(notification.created_at))}
                    </div>
                  </div>

                  {/* Actions */}
                  {notification.status !== 'read' && (
                    <button
                      onClick={(e) => handleMarkAsRead(notification.id, e)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#2563eb',
                        cursor: 'pointer',
                        fontSize: '20px',
                        padding: 0,
                        display: 'flex',
                        alignItems: 'center',
                        flexShrink: 0,
                        width: '24px',
                        height: '24px'
                      }}
                      title="Mark as read"
                    >
                      ✓
                    </button>
                  )}

                  <button
                    onClick={(e) => handleDeleteNotification(notification.id, e)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#999',
                      cursor: 'pointer',
                      fontSize: '16px',
                      padding: 0,
                      display: 'flex',
                      alignItems: 'center',
                      flexShrink: 0,
                      width: '20px',
                      height: '20px'
                    }}
                    title="Delete"
                  >
                    ✕
                  </button>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div style={{
              padding: '12px 16px',
              borderTop: '1px solid #e0e0e0',
              textAlign: 'center'
            }}>
              <button
                onClick={() => {
                  onNotificationClick?.();
                  setShowDropdown(false);
                }}
                style={{
                  width: '100%',
                  padding: '8px 16px',
                  backgroundColor: '#2563eb',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: 'bold'
                }}
              >
                View All Notifications
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Helper function to get relative time
function getRelativeTime(date) {
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString();
}

export default NotificationBell;
