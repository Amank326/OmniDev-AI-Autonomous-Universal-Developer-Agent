/**
 * Phase 26: Member Presence Component
 * Live member status display with activity indicators and hover info
 */

import React, { useState, useEffect, useCallback } from 'react';

const MemberPresence = ({ workspaceId, userId, apiBaseUrl = 'http://localhost:5000' }) => {
  // State
  const [members, setMembers] = useState([]);
  const [presence, setPresence] = useState({});
  const [hoveredMember, setHoveredMember] = useState(null);
  const [memberActivity, setMemberActivity] = useState({});
  const [loading, setLoading] = useState(false);
  
  // View options
  const [viewMode, setViewMode] = useState('grid'); // grid or list
  const [filterStatus, setFilterStatus] = useState('all'); // all, active, idle, away
  const [searchQuery, setSearchQuery] = useState('');


  // ========================================================================
  // LIFECYCLE
  // ========================================================================

  useEffect(() => {
    loadMembers();
    loadPresence();
    
    // Poll presence every 30 seconds
    const interval = setInterval(() => {
      loadPresence();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [workspaceId]);


  // ========================================================================
  // DATA LOADING
  // ========================================================================

  const loadMembers = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}/members`
      );
      const data = await response.json();
      setMembers(data.members || []);
    } catch (error) {
      console.error('Failed to load members:', error);
    } finally {
      setLoading(false);
    }
  }, [workspaceId, apiBaseUrl]);

  const loadPresence = useCallback(async () => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}/presence`
      );
      const data = await response.json();
      setPresence(data.presence || {});
      setMemberActivity(data.activity || {});
    } catch (error) {
      console.error('Failed to load presence:', error);
    }
  }, [workspaceId, apiBaseUrl]);

  const handleMentionUser = useCallback((memberId) => {
    // Trigger mention in parent component or emit event
    console.log(`Mentioned: ${memberId}`);
  }, []);


  // ========================================================================
  // HELPERS
  // ========================================================================

  const getMemberAvatar = (memberId) => {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F'];
    const color = colors[memberId.charCodeAt(0) % colors.length];
    const initials = memberId
      .split(/[._-]/)
      .map(part => part.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);

    return { color, initials };
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return '#2ecc71';
      case 'idle': return '#f39c12';
      case 'away': return '#e67e22';
      case 'offline': return '#95a5a6';
      default: return '#bdc3c7';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return '●';
      case 'idle': return '◐';
      case 'away': return '◯';
      case 'offline': return '○';
      default: return '?';
    }
  };

  const getActivityText = (memberId) => {
    const activity = memberActivity[memberId];
    if (!activity) return 'No recent activity';
    
    return activity.current_view || activity.last_action || 'Viewing workspace';
  };

  const getLastActivityTime = (memberId) => {
    const activity = memberActivity[memberId];
    if (!activity) return 'Never';
    
    // Parse timestamp and calculate relative time
    const timestamp = new Date(activity.timestamp);
    const now = new Date();
    const diff = Math.floor((now - timestamp) / 1000); // seconds
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return 'Long ago';
  };

  const filteredMembers = members.filter(member => {
    const memberPresence = presence[member.user_id];
    const status = memberPresence?.status || 'offline';
    
    // Filter by status
    if (filterStatus !== 'all' && status !== filterStatus) {
      return false;
    }
    
    // Filter by search
    if (searchQuery && !member.user_id.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    
    return true;
  });

  // Statistics
  const activeCount = members.filter(m => presence[m.user_id]?.status === 'active').length;
  const idleCount = members.filter(m => presence[m.user_id]?.status === 'idle').length;
  const awayCount = members.filter(m => presence[m.user_id]?.status === 'away').length;


  // ========================================================================
  // RENDER: MEMBER CARD (Grid View)
  // ========================================================================

  const renderMemberCard = (member) => {
    const memberPresence = presence[member.user_id];
    const status = memberPresence?.status || 'offline';
    const { color, initials } = getMemberAvatar(member.user_id);
    const isHovered = hoveredMember === member.user_id;

    return (
      <div
        key={member.user_id}
        onMouseEnter={() => setHoveredMember(member.user_id)}
        onMouseLeave={() => setHoveredMember(null)}
        style={{
          position: 'relative',
          padding: '15px',
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: isHovered ? '0 4px 12px rgba(0,0,0,0.15)' : '0 2px 4px rgba(0,0,0,0.1)',
          cursor: 'pointer',
          transition: 'all 0.2s',
          transform: isHovered ? 'translateY(-4px)' : 'translateY(0)'
        }}
      >
        {/* Avatar */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          marginBottom: '12px',
          position: 'relative'
        }}>
          <div style={{
            width: '60px',
            height: '60px',
            borderRadius: '50%',
            backgroundColor: color,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '18px',
            fontWeight: 'bold',
            boxShadow: '0 2px 6px rgba(0,0,0,0.15)'
          }}>
            {initials}
          </div>
          
          {/* Status Badge */}
          <div style={{
            position: 'absolute',
            bottom: '0',
            right: '0',
            width: '16px',
            height: '16px',
            borderRadius: '50%',
            backgroundColor: getStatusColor(status),
            border: '2px solid white',
            boxShadow: '0 1px 3px rgba(0,0,0,0.2)'
          }} />
        </div>

        {/* Name & Role */}
        <div style={{ textAlign: 'center', marginBottom: '8px' }}>
          <div style={{
            fontWeight: '600',
            fontSize: '13px',
            marginBottom: '2px',
            color: '#2c3e50'
          }}>
            {member.user_id}
          </div>
          <div style={{
            fontSize: '11px',
            color: '#999',
            textTransform: 'capitalize'
          }}>
            {member.role || 'member'}
          </div>
        </div>

        {/* Status Text */}
        <div style={{
          fontSize: '11px',
          color: getStatusColor(status),
          fontWeight: '600',
          textAlign: 'center',
          marginBottom: '8px'
        }}>
          {getStatusIcon(status)} {status.toUpperCase()}
        </div>

        {/* Hover Info */}
        {isHovered && (
          <div style={{
            padding: '12px',
            marginTop: '8px',
            borderTop: '1px solid #eee',
            backgroundColor: '#f9f9f9',
            borderRadius: '4px',
            fontSize: '11px',
            color: '#666'
          }}>
            <div style={{ marginBottom: '6px' }}>
              <strong>Activity:</strong>
              <div style={{ color: '#999', marginTop: '2px' }}>
                {getActivityText(member.user_id)}
              </div>
            </div>
            <div style={{ marginBottom: '8px' }}>
              <strong>Last active:</strong>
              <div style={{ color: '#999', marginTop: '2px' }}>
                {getLastActivityTime(member.user_id)}
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '6px', marginTop: '8px' }}>
              <button
                onClick={() => handleMentionUser(member.user_id)}
                style={{
                  flex: 1,
                  padding: '6px 8px',
                  backgroundColor: '#3498db',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  fontSize: '10px',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                @ Mention
              </button>
              <button
                style={{
                  flex: 1,
                  padding: '6px 8px',
                  backgroundColor: '#f0f0f0',
                  color: '#666',
                  border: 'none',
                  borderRadius: '3px',
                  fontSize: '10px',
                  cursor: 'pointer'
                }}
              >
                Profile
              </button>
            </div>
          </div>
        )}
      </div>
    );
  };


  // ========================================================================
  // RENDER: MEMBER ROW (List View)
  // ========================================================================

  const renderMemberRow = (member) => {
    const memberPresence = presence[member.user_id];
    const status = memberPresence?.status || 'offline';
    const { color, initials } = getMemberAvatar(member.user_id);

    return (
      <div
        key={member.user_id}
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '12px 16px',
          borderBottom: '1px solid #eee',
          backgroundColor: 'white',
          cursor: 'pointer',
          transition: 'all 0.2s',
          ':hover': {
            backgroundColor: '#f9f9f9'
          }
        }}
        onMouseEnter={() => setHoveredMember(member.user_id)}
        onMouseLeave={() => setHoveredMember(null)}
      >
        {/* Avatar */}
        <div style={{ position: 'relative', marginRight: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            backgroundColor: color,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '13px',
            fontWeight: 'bold'
          }}>
            {initials}
          </div>
          <div style={{
            position: 'absolute',
            bottom: '-2px',
            right: '-2px',
            width: '12px',
            height: '12px',
            borderRadius: '50%',
            backgroundColor: getStatusColor(status),
            border: '2px solid white'
          }} />
        </div>

        {/* Info */}
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: '600', fontSize: '13px', marginBottom: '2px' }}>
            {member.user_id}
          </div>
          <div style={{ fontSize: '11px', color: '#999' }}>
            {getActivityText(member.user_id)}
          </div>
        </div>

        {/* Status Badge */}
        <div style={{
          display: 'inline-block',
          padding: '4px 10px',
          backgroundColor: getStatusColor(status),
          color: 'white',
          borderRadius: '3px',
          fontSize: '10px',
          fontWeight: '600',
          marginRight: '12px',
          textTransform: 'uppercase'
        }}>
          {getStatusIcon(status)} {status}
        </div>

        {/* Actions */}
        {hoveredMember === member.user_id && (
          <div style={{ display: 'flex', gap: '6px' }}>
            <button
              onClick={() => handleMentionUser(member.user_id)}
              style={{
                padding: '6px 10px',
                backgroundColor: '#3498db',
                color: 'white',
                border: 'none',
                borderRadius: '3px',
                fontSize: '11px',
                cursor: 'pointer'
              }}
            >
              Mention
            </button>
          </div>
        )}

        {/* Time */}
        <div style={{ fontSize: '11px', color: '#999', minWidth: '70px', textAlign: 'right' }}>
          {getLastActivityTime(member.user_id)}
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
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '20px' }}>
          <h1 style={{ margin: '0 0 10px 0' }}>Team Presence</h1>
          <p style={{ color: '#666', margin: 0 }}>
            {activeCount} active • {idleCount} idle • {awayCount} away • {members.length - activeCount - idleCount - awayCount} offline
          </p>
        </div>

        {/* Controls */}
        <div style={{
          display: 'flex',
          gap: '12px',
          marginBottom: '20px',
          flexWrap: 'wrap'
        }}>
          {/* Search */}
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search members..."
            style={{
              flex: 1,
              minWidth: '200px',
              padding: '10px 12px',
              borderRadius: '4px',
              border: '1px solid #bdc3c7',
              backgroundColor: 'white'
            }}
          />

          {/* Filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            style={{
              padding: '10px 12px',
              borderRadius: '4px',
              border: '1px solid #bdc3c7',
              backgroundColor: 'white'
            }}
          >
            <option value="all">All Status</option>
            <option value="active">Active Only</option>
            <option value="idle">Idle</option>
            <option value="away">Away</option>
            <option value="offline">Offline</option>
          </select>

          {/* View Mode */}
          <div style={{ display: 'flex', gap: '6px' }}>
            <button
              onClick={() => setViewMode('grid')}
              style={{
                padding: '10px 12px',
                backgroundColor: viewMode === 'grid' ? '#3498db' : '#f0f0f0',
                color: viewMode === 'grid' ? 'white' : '#666',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: '600'
              }}
            >
              ⊞ Grid
            </button>
            <button
              onClick={() => setViewMode('list')}
              style={{
                padding: '10px 12px',
                backgroundColor: viewMode === 'list' ? '#3498db' : '#f0f0f0',
                color: viewMode === 'list' ? 'white' : '#666',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: '600'
              }}
            >
              ≡ List
            </button>
          </div>
        </div>

        {/* Members Display */}
        {loading ? (
          <div style={{ textAlign: 'center', color: '#999', padding: '40px' }}>
            Loading members...
          </div>
        ) : viewMode === 'grid' ? (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
            gap: '15px'
          }}>
            {filteredMembers.map(member => renderMemberCard(member))}
          </div>
        ) : (
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            overflow: 'hidden',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            {filteredMembers.map(member => renderMemberRow(member))}
          </div>
        )}

        {/* Empty State */}
        {filteredMembers.length === 0 && !loading && (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            backgroundColor: 'white',
            borderRadius: '8px',
            color: '#999'
          }}>
            No members found matching your filters
          </div>
        )}
      </div>
    </div>
  );
};

export default MemberPresence;
