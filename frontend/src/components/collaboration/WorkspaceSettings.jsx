/**
 * Phase 26: Workspace Settings Component
 * Member management, permissions, templates, invitations, exports
 */

import React, { useState, useEffect, useCallback } from 'react';

const WorkspaceSettings = ({ workspaceId, userId, apiBaseUrl = 'http://localhost:5000' }) => {
  // Data state
  const [workspace, setWorkspace] = useState(null);
  const [members, setMembers] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [activityLog, setActivityLog] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // UI state
  const [activeTab, setActiveTab] = useState('members');
  const [editingMember, setEditingMember] = useState(null);
  const [inviteEmail, setInviteEmail] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [exportFormat, setExportFormat] = useState('json');
  
  // Modals
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);


  // ========================================================================
  // LIFECYCLE
  // ========================================================================

  useEffect(() => {
    loadWorkspaceData();
  }, [workspaceId]);


  // ========================================================================
  // DATA LOADING
  // ========================================================================

  const loadWorkspaceData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Load workspace
      const wsRes = await fetch(`${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}`);
      setWorkspace(await wsRes.json());
      
      // Load members
      const memRes = await fetch(`${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}/members`);
      setMembers((await memRes.json()).members || []);
      
      // Load templates
      const tplRes = await fetch(`${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}/templates`);
      setTemplates((await tplRes.json()).templates || []);
      
      // Load activity log
      const actRes = await fetch(
        `${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}/activity?limit=50`
      );
      setActivityLog((await actRes.json()).activity || []);
    } catch (error) {
      console.error('Failed to load workspace data:', error);
    } finally {
      setLoading(false);
    }
  }, [workspaceId, apiBaseUrl]);


  // ========================================================================
  // MEMBER MANAGEMENT
  // ========================================================================

  const roles = [
    { value: 'admin', label: 'Admin', permissions: 'Full access' },
    { value: 'analyst', label: 'Analyst', permissions: 'Create & edit' },
    { value: 'viewer', label: 'Viewer', permissions: 'View only' },
    { value: 'guest', label: 'Guest', permissions: 'Limited access' }
  ];

  const handleUpdateMemberRole = useCallback(async (memberId, newRole) => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}/members/${memberId}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ role: newRole })
        }
      );

      if (response.ok) {
        loadWorkspaceData();
        setEditingMember(null);
      }
    } catch (error) {
      console.error('Failed to update member:', error);
    }
  }, [workspaceId, apiBaseUrl, loadWorkspaceData]);

  const handleRemoveMember = useCallback(async (memberId) => {
    if (!window.confirm('Are you sure you want to remove this member?')) return;

    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}/members/${memberId}`,
        { method: 'DELETE' }
      );

      if (response.ok) {
        loadWorkspaceData();
      }
    } catch (error) {
      console.error('Failed to remove member:', error);
    }
  }, [workspaceId, apiBaseUrl, loadWorkspaceData]);

  const handleSendInvite = useCallback(async () => {
    if (!inviteEmail) return;

    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}/invitations`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: inviteEmail,
            invited_by: userId
          })
        }
      );

      if (response.ok) {
        setInviteEmail('');
        setShowInviteModal(false);
        // Show success message
      }
    } catch (error) {
      console.error('Failed to send invite:', error);
    }
  }, [inviteEmail, workspaceId, userId, apiBaseUrl]);


  // ========================================================================
  // EXPORT/IMPORT
  // ========================================================================

  const handleExport = useCallback(async () => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}/export`,
        { method: 'POST' }
      );

      const data = await response.json();
      const dataStr = JSON.stringify(data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `workspace-${workspaceId}-${new Date().toISOString()}.json`;
      link.click();
    } catch (error) {
      console.error('Failed to export workspace:', error);
    }
  }, [workspaceId, apiBaseUrl]);


  // ========================================================================
  // RENDER: MEMBERS TAB
  // ========================================================================

  const renderMembersTab = () => {
    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ margin: 0 }}>Workspace Members ({members.length})</h3>
          <button
            onClick={() => setShowInviteModal(true)}
            style={{
              padding: '10px 16px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            + Invite Member
          </button>
        </div>

        {/* Members Table */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          overflow: 'hidden',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8f9fa', borderBottom: '2px solid #ddd' }}>
                <th style={{ padding: '15px', textAlign: 'left', fontWeight: '600' }}>Member</th>
                <th style={{ padding: '15px', textAlign: 'left', fontWeight: '600' }}>Role</th>
                <th style={{ padding: '15px', textAlign: 'left', fontWeight: '600' }}>Permissions</th>
                <th style={{ padding: '15px', textAlign: 'center', fontWeight: '600' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {members.map(member => (
                <tr key={member.user_id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '15px' }}>
                    <div style={{ fontWeight: '500' }}>{member.user_id}</div>
                    <div style={{ fontSize: '12px', color: '#999' }}>
                      Joined {member.joined_date || 'recently'}
                    </div>
                  </td>
                  <td style={{ padding: '15px' }}>
                    {editingMember === member.user_id ? (
                      <select
                        value={member.role}
                        onChange={(e) => handleUpdateMemberRole(member.user_id, e.target.value)}
                        style={{
                          padding: '6px 10px',
                          borderRadius: '4px',
                          border: '1px solid #bdc3c7'
                        }}
                      >
                        {roles.map(r => (
                          <option key={r.value} value={r.value}>{r.label}</option>
                        ))}
                      </select>
                    ) : (
                      <span style={{
                        display: 'inline-block',
                        padding: '4px 12px',
                        backgroundColor: '#e8f4f8',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: '600',
                        color: '#3498db'
                      }}>
                        {roles.find(r => r.value === member.role)?.label || member.role}
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '15px', fontSize: '12px', color: '#666' }}>
                    {roles.find(r => r.value === member.role)?.permissions}
                  </td>
                  <td style={{ padding: '15px', textAlign: 'center' }}>
                    <button
                      onClick={() => setEditingMember(editingMember === member.user_id ? null : member.user_id)}
                      style={{
                        padding: '6px 12px',
                        backgroundColor: editingMember === member.user_id ? '#f39c12' : '#f0f0f0',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px',
                        marginRight: '5px',
                        color: editingMember === member.user_id ? 'white' : '#666'
                      }}
                    >
                      {editingMember === member.user_id ? 'Done' : 'Edit'}
                    </button>
                    {member.user_id !== userId && (
                      <button
                        onClick={() => handleRemoveMember(member.user_id)}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: '#e74c3c',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        Remove
                      </button>
                    )}
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
  // RENDER: TEMPLATES TAB
  // ========================================================================

  const renderTemplatesTab = () => {
    const defaultTemplates = [
      {
        id: 'ecommerce',
        name: 'E-commerce',
        description: 'Sales, inventory, and customer metrics',
        metrics: ['Revenue', 'Orders', 'Conversion Rate', 'Cart Abandonment']
      },
      {
        id: 'saas',
        name: 'SaaS',
        description: 'MRR, churn, and customer health',
        metrics: ['MRR', 'Churn Rate', 'CAC', 'LTV']
      },
      {
        id: 'marketing',
        name: 'Marketing',
        description: 'Campaign performance and engagement',
        metrics: ['Impressions', 'CTR', 'Leads', 'CAC']
      }
    ];

    return (
      <div>
        <h3 style={{ marginTop: 0 }}>Workspace Templates</h3>
        <p style={{ color: '#666' }}>
          Use pre-built templates to quickly set up your workspace with common metrics and dashboards.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '15px' }}>
          {defaultTemplates.map(template => (
            <div
              key={template.id}
              style={{
                padding: '20px',
                backgroundColor: selectedTemplate === template.id ? '#e8f4f8' : 'white',
                border: selectedTemplate === template.id ? '2px solid #3498db' : '1px solid #ddd',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onClick={() => setSelectedTemplate(template.id)}
            >
              <h4 style={{ margin: '0 0 8px 0' }}>{template.name}</h4>
              <p style={{ margin: '0 0 12px 0', fontSize: '12px', color: '#666' }}>
                {template.description}
              </p>
              
              <div style={{ fontSize: '12px', marginBottom: '12px' }}>
                <strong>Includes:</strong>
                {template.metrics.map(metric => (
                  <div key={metric} style={{ color: '#999' }}>• {metric}</div>
                ))}
              </div>

              <button
                style={{
                  width: '100%',
                  padding: '8px',
                  backgroundColor: selectedTemplate === template.id ? '#3498db' : '#f0f0f0',
                  color: selectedTemplate === template.id ? 'white' : '#666',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '12px'
                }}
              >
                {selectedTemplate === template.id ? '✓ Selected' : 'Select'}
              </button>
            </div>
          ))}
        </div>
      </div>
    );
  };


  // ========================================================================
  // RENDER: ACTIVITY LOG TAB
  // ========================================================================

  const renderActivityLogTab = () => {
    return (
      <div>
        <h3 style={{ marginTop: 0 }}>Activity Log</h3>
        
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          overflow: 'hidden',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
            {activityLog.map(activity => (
              <div
                key={activity.id || Math.random()}
                style={{
                  padding: '15px',
                  borderBottom: '1px solid #eee',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <div style={{ fontWeight: '500', marginBottom: '4px' }}>
                    {activity.user_id} {activity.action}
                  </div>
                  <div style={{ fontSize: '12px', color: '#999' }}>
                    {activity.description || activity.resource}
                  </div>
                </div>
                <div style={{ fontSize: '12px', color: '#999', whiteSpace: 'nowrap' }}>
                  {activity.timestamp}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };


  // ========================================================================
  // RENDER: EXPORT/IMPORT TAB
  // ========================================================================

  const renderExportTab = () => {
    return (
      <div>
        <h3 style={{ marginTop: 0 }}>Export & Import</h3>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '20px'
        }}>
          {/* Export Section */}
          <div style={{
            padding: '20px',
            backgroundColor: 'white',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <h4 style={{ marginTop: 0 }}>Export Workspace Configuration</h4>
            <p style={{ color: '#666', fontSize: '12px' }}>
              Download your workspace configuration, dashboards, and metrics as a JSON file.
              Perfect for backing up or sharing settings.
            </p>

            <button
              onClick={handleExport}
              style={{
                padding: '10px 16px',
                backgroundColor: '#27ae60',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: '600'
              }}
            >
              📥 Export Now
            </button>
          </div>

          {/* Import Section */}
          <div style={{
            padding: '20px',
            backgroundColor: 'white',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <h4 style={{ marginTop: 0 }}>Import Configuration</h4>
            <p style={{ color: '#666', fontSize: '12px' }}>
              Import a previously exported workspace configuration to quickly set up
              dashboards and metrics.
            </p>

            <button
              style={{
                padding: '10px 16px',
                backgroundColor: '#f39c12',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: '600'
              }}
            >
              📤 Import
            </button>
          </div>
        </div>
      </div>
    );
  };


  // ========================================================================
  // RENDER: MODALS
  // ========================================================================

  const renderInviteModal = () => {
    if (!showInviteModal) return null;

    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0,0,0,0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000
      }}>
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '30px',
          maxWidth: '400px',
          width: '90%',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
        }}>
          <h2 style={{ marginTop: 0 }}>Invite Member</h2>
          
          <input
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            placeholder="member@example.com"
            style={{
              width: '100%',
              padding: '10px',
              marginBottom: '15px',
              borderRadius: '4px',
              border: '1px solid #bdc3c7',
              boxSizing: 'border-box'
            }}
          />

          <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
            <button
              onClick={() => setShowInviteModal(false)}
              style={{
                padding: '10px 16px',
                backgroundColor: '#f0f0f0',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleSendInvite}
              style={{
                padding: '10px 16px',
                backgroundColor: '#3498db',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: '600'
              }}
            >
              Send Invite
            </button>
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
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '30px' }}>
          <h1 style={{ margin: 0 }}>Workspace Settings</h1>
          <p style={{ color: '#666', marginTop: '5px' }}>
            {workspace?.name || 'Loading...'} • ID: {workspaceId}
          </p>
        </div>

        {/* Tabs */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          overflow: 'hidden'
        }}>
          {/* Tab Buttons */}
          <div style={{
            display: 'flex',
            borderBottom: '2px solid #eee',
            backgroundColor: '#f9f9f9'
          }}>
            {['members', 'templates', 'activity', 'export'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  padding: '15px 20px',
                  backgroundColor: activeTab === tab ? 'white' : 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  fontWeight: activeTab === tab ? '600' : '400',
                  color: activeTab === tab ? '#3498db' : '#999',
                  borderBottom: activeTab === tab ? '3px solid #3498db' : 'none',
                  marginBottom: activeTab === tab ? '-2px' : '0'
                }}
              >
                {tab.toUpperCase()}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div style={{ padding: '30px' }}>
            {activeTab === 'members' && renderMembersTab()}
            {activeTab === 'templates' && renderTemplatesTab()}
            {activeTab === 'activity' && renderActivityLogTab()}
            {activeTab === 'export' && renderExportTab()}
          </div>
        </div>
      </div>

      {/* Modals */}
      {renderInviteModal()}

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

export default WorkspaceSettings;
