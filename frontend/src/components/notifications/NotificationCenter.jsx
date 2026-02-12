import React, { useState, useEffect, useCallback } from 'react';

const NotificationCenter = () => {
  const [notifications, setNotifications] = useState([]);
  const [filteredNotifications, setFilteredNotifications] = useState([]);
  const [selectedNotification, setSelectedNotification] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedCount, setSelectedCount] = useState(0);
  const [selectedNotifications, setSelectedNotifications] = useState(new Set());

  // Fetch notifications
  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/notification/notifications?user_id=current&limit=100');
      const data = await response.json();
      setNotifications(data.data || []);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Apply filters
  useEffect(() => {
    let filtered = notifications;

    if (filterType !== 'all') {
      filtered = filtered.filter(n => n.type === filterType);
    }

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter(n => 
        n.title.toLowerCase().includes(q) || 
        n.body.toLowerCase().includes(q)
      );
    }

    setFilteredNotifications(filtered);
  }, [notifications, filterType, searchQuery]);

  const handleNotificationClick = (notification) => {
    setSelectedNotification(notification);
    if (notification.status !== 'read') {
      markAsRead(notification.id);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await fetch(`/api/v1/notification/notifications/${notificationId}/read`, {
        method: 'PUT'
      });
      setNotifications(prev =>
        prev.map(n => n.id === notificationId ? { ...n, status: 'read' } : n)
      );
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const deleteNotification = async (notificationId, e) => {
    e.stopPropagation();
    try {
      await fetch(`/api/v1/notification/notifications/${notificationId}`, {
        method: 'DELETE'
      });
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
      if (selectedNotification?.id === notificationId) {
        setSelectedNotification(null);
      }
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  const toggleNotificationSelection = (notificationId, e) => {
    e.stopPropagation();
    const newSelected = new Set(selectedNotifications);
    if (newSelected.has(notificationId)) {
      newSelected.delete(notificationId);
    } else {
      newSelected.add(notificationId);
    }
    setSelectedNotifications(newSelected);
    setSelectedCount(newSelected.size);
  };

  const bulkMarkRead = async () => {
    if (selectedCount === 0) return;
    try {
      await fetch('/api/v1/notification/notifications/bulk-read', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'current',
          notification_ids: Array.from(selectedNotifications)
        })
      });
      setNotifications(prev =>
        prev.map(n =>
          selectedNotifications.has(n.id) ? { ...n, status: 'read' } : n
        )
      );
      setSelectedNotifications(new Set());
      setSelectedCount(0);
    } catch (error) {
      console.error('Failed to bulk mark read:', error);
    }
  };

  const unreadCount = notifications.filter(n => n.status !== 'read').length;
  const types = ['all', 'alert', 'mention', 'update', 'system'];

  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: '#f5f5f5' }}>
      {/* Sidebar - Filters */}
      <div style={{
        width: '260px',
        borderRight: '1px solid #e0e0e0',
        backgroundColor: 'white',
        padding: '20px',
        overflowY: 'auto'
      }}>
        <h2 style={{ margin: '0 0 20px 0', fontSize: '18px', fontWeight: 'bold' }}>
          Notification Center
        </h2>

        {/* Unread Badge */}
        <div style={{
          backgroundColor: '#2563eb',
          color: 'white',
          padding: '12px',
          borderRadius: '8px',
          marginBottom: '20px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{unreadCount}</div>
          <div style={{ fontSize: '12px', marginTop: '4px' }}>Unread</div>
        </div>

        {/* Filter Section */}
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ fontSize: '12px', fontWeight: 'bold', color: '#666', marginBottom: '8px', textTransform: 'uppercase' }}>
            Filter by Type
          </h3>
          {types.map(type => (
            <button key={type}
              onClick={() => setFilterType(type)}
              style={{
                display: 'block',
                width: '100%',
                padding: '8px 12px',
                marginBottom: '4px',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: filterType === type ? '#2563eb' : '#f0f0f0',
                color: filterType === type ? 'white' : '#333',
                cursor: 'pointer',
                textAlign: 'left',
                fontSize: '14px',
                transition: 'all 0.2s'
              }}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>

        {/* Search */}
        <div style={{ marginBottom: '20px' }}>
          <input
            type="text"
            placeholder="Search notifications..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #e0e0e0',
              borderRadius: '6px',
              fontSize: '14px',
              boxSizing: 'border-box'
            }}
          />
        </div>

        {/* Bulk Actions */}
        {selectedCount > 0 && (
          <div style={{
            padding: '12px',
            backgroundColor: '#f0f7ff',
            borderRadius: '6px',
            borderLeft: '3px solid #2563eb',
            marginBottom: '20px'
          }}>
            <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '8px' }}>
              {selectedCount} selected
            </div>
            <button
              onClick={bulkMarkRead}
              style={{
                width: '100%',
                padding: '6px 12px',
                backgroundColor: '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: 'bold',
                cursor: 'pointer'
              }}
            >
              Mark as Read
            </button>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Notifications List */}
        <div style={{
          flex: selectedNotification ? 0.4 : 1,
          borderRight: selectedNotification ? '1px solid #e0e0e0' : 'none',
          overflow: 'auto',
          backgroundColor: 'white'
        }}>
          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center' }}>
              <div style={{ fontSize: '16px', color: '#666' }}>Loading notifications...</div>
            </div>
          ) : filteredNotifications.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center' }}>
              <div style={{ fontSize: '16px', color: '#999' }}>No notifications</div>
            </div>
          ) : (
            <div>
              {filteredNotifications.map((notification) => (
                <div
                  key={notification.id}
                  onClick={() => handleNotificationClick(notification)}
                  style={{
                    padding: '16px',
                    borderBottom: '1px solid #f0f0f0',
                    backgroundColor: selectedNotification?.id === notification.id ? '#f0f7ff' : (notification.status === 'read' ? 'white' : '#fafafa'),
                    cursor: 'pointer',
                    transition: 'background-color 0.2s',
                    display: 'flex',
                    gap: '12px'
                  }}
                >
                  {/* Unread Indicator */}
                  {notification.status !== 'read' && (
                    <div style={{
                      width: '8px',
                      height: '8px',
                      backgroundColor: '#2563eb',
                      borderRadius: '50%',
                      marginTop: '4px',
                      flexShrink: 0
                    }} />
                  )}

                  {/* Content */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    {/* Checkbox */}
                    <input
                      type="checkbox"
                      checked={selectedNotifications.has(notification.id)}
                      onChange={(e) => toggleNotificationSelection(notification.id, e)}
                      onClick={(e) => e.stopPropagation()}
                      style={{ marginRight: '8px', cursor: 'pointer' }}
                    />

                    <h4 style={{
                      margin: '0 0 4px 0',
                      fontSize: '14px',
                      fontWeight: notification.status === 'read' ? 'normal' : 'bold',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {notification.title}
                    </h4>

                    <p style={{
                      margin: '4px 0 0 0',
                      fontSize: '13px',
                      color: '#666',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {notification.body}
                    </p>

                    <div style={{
                      marginTop: '4px',
                      fontSize: '12px',
                      color: '#999'
                    }}>
                      {new Date(notification.created_at).toLocaleString()}
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{
                    display: 'flex',
                    gap: '8px',
                    flexShrink: 0
                  }}>
                    <span style={{
                      padding: '2px 6px',
                      backgroundColor: '#f0f0f0',
                      borderRadius: '4px',
                      fontSize: '11px',
                      color: '#666'
                    }}>
                      {notification.type}
                    </span>
                    <button
                      onClick={(e) => deleteNotification(notification.id, e)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#999',
                        cursor: 'pointer',
                        fontSize: '16px',
                        padding: 0
                      }}
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detail View */}
        {selectedNotification && (
          <div style={{
            width: '60%',
            padding: '24px',
            overflow: 'auto',
            backgroundColor: 'white'
          }}>
            <h2 style={{ margin: '0 0 16px 0', fontSize: '20px', fontWeight: 'bold' }}>
              {selectedNotification.title}
            </h2>

            <div style={{
              display: 'flex',
              gap: '12px',
              marginBottom: '20px',
              flexWrap: 'wrap'
            }}>
              <span style={{
                padding: '4px 12px',
                backgroundColor: '#f0f0f0',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                {selectedNotification.type}
              </span>
              <span style={{
                padding: '4px 12px',
                backgroundColor: '#f0f0f0',
                borderRadius: '4px',
                fontSize: '12px'
              }}>
                {selectedNotification.status}
              </span>
              <span style={{
                padding: '4px 12px',
                backgroundColor: '#f0f0f0',
                borderRadius: '4px',
                fontSize: '12px',
                color: '#666'
              }}>
                {new Date(selectedNotification.created_at).toLocaleString()}
              </span>
            </div>

            <div style={{
              fontSize: '14px',
              lineHeight: '1.6',
              color: '#333',
              marginBottom: '20px'
            }}>
              {selectedNotification.body}
            </div>

            {selectedNotification.action_url && (
              <a href={selectedNotification.action_url}
                style={{
                  display: 'inline-block',
                  padding: '10px 16px',
                  backgroundColor: '#2563eb',
                  color: 'white',
                  textDecoration: 'none',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                View Detail
              </a>
            )}

            <button
              onClick={(e) => deleteNotification(selectedNotification.id, e)}
              style={{
                marginLeft: '8px',
                padding: '10px 16px',
                backgroundColor: '#f0f0f0',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              Delete
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationCenter;
