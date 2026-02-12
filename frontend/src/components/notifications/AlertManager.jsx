import React, { useState, useEffect, useCallback } from 'react';

const AlertManager = () => {
  const [rules, setRules] = useState([]);
  const [selectedRule, setSelectedRule] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTestModal, setShowTestModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    severity: 'warning',
    logical_operator: 'AND',
    cooldown_minutes: 15,
    conditions: [{ field: '', operator: '>', value: '' }],
    notification_channels: ['in_app']
  });

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/notification/rules');
      const data = await response.json();
      setRules(data.data || []);
    } catch (error) {
      console.error('Failed to fetch rules:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleAddCondition = () => {
    setFormData(prev => ({
      ...prev,
      conditions: [...prev.conditions, { field: '', operator: '>', value: '' }]
    }));
  };

  const handleRemoveCondition = (index) => {
    setFormData(prev => ({
      ...prev,
      conditions: prev.conditions.filter((_, i) => i !== index)
    }));
  };

  const handleConditionChange = (index, field, value) => {
    setFormData(prev => {
      const newConditions = [...prev.conditions];
      newConditions[index] = { ...newConditions[index], [field]: value };
      return { ...prev, conditions: newConditions };
    });
  };

  const handleChannelToggle = (channel) => {
    setFormData(prev => {
      const channels = prev.notification_channels.includes(channel)
        ? prev.notification_channels.filter(c => c !== channel)
        : [...prev.notification_channels, channel];
      return { ...prev, notification_channels: channels };
    });
  };

  const handleCreateRule = async () => {
    try {
      const response = await fetch('/api/v1/notification/rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          created_by: 'current_user'
        })
      });

      if (response.ok) {
        fetchRules();
        setShowCreateModal(false);
        resetForm();
      }
    } catch (error) {
      console.error('Failed to create rule:', error);
    }
  };

  const handleUpdateRule = async () => {
    if (!selectedRule) return;
    try {
      const response = await fetch(`/api/v1/notification/rules/${selectedRule.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...selectedRule,
          ...formData
        })
      });

      if (response.ok) {
        fetchRules();
        setSelectedRule(null);
      }
    } catch (error) {
      console.error('Failed to update rule:', error);
    }
  };

  const handleDeleteRule = async (ruleId) => {
    if (!window.confirm('Delete this rule?')) return;
    try {
      await fetch(`/api/v1/notification/rules/${ruleId}`, {
        method: 'DELETE'
      });
      fetchRules();
      if (selectedRule?.id === ruleId) {
        setSelectedRule(null);
      }
    } catch (error) {
      console.error('Failed to delete rule:', error);
    }
  };

  const handleTestRule = async () => {
    if (!selectedRule) return;
    try {
      const response = await fetch(`/api/v1/notification/rules/${selectedRule.id}/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data: {
            status: 'high',
            value: 95
          }
        })
      });
      const data = await response.json();
      setTestResult(data);
    } catch (error) {
      console.error('Failed to test rule:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      severity: 'warning',
      logical_operator: 'AND',
      cooldown_minutes: 15,
      conditions: [{ field: '', operator: '>', value: '' }],
      notification_channels: ['in_app']
    });
  };

  const operators = ['>', '<', '>=', '<=', '==', '!=', 'contains', 'in_list'];
  const channels = ['email', 'sms', 'push', 'in_app'];
  const severities = ['info', 'warning', 'critical', 'urgent'];

  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: '#f5f5f5' }}>
      {/* List Sidebar */}
      <div style={{
        width: '280px',
        borderRight: '1px solid #e0e0e0',
        backgroundColor: 'white',
        padding: '20px',
        overflowY: 'auto'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 'bold' }}>Alert Rules</h2>
          <button
            onClick={() => { resetForm(); setShowCreateModal(true); }}
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
            + New
          </button>
        </div>

        {loading ? (
          <div style={{ color: '#999' }}>Loading...</div>
        ) : (
          <div>
            {rules.map(rule => (
              <div
                key={rule.id}
                onClick={() => { setSelectedRule(rule); setFormData(rule); }}
                style={{
                  padding: '12px',
                  marginBottom: '8px',
                  backgroundColor: selectedRule?.id === rule.id ? '#f0f7ff' : '#f5f5f5',
                  borderLeft: selectedRule?.id === rule.id ? '3px solid #2563eb' : '3px solid transparent',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '4px' }}>
                  {rule.name}
                </div>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                  {rule.description}
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span style={{
                    padding: '2px 6px',
                    backgroundColor: '#dbeafe',
                    borderRadius: '3px',
                    fontSize: '11px',
                    color: '#1e40af'
                  }}>
                    {rule.severity}
                  </span>
                  {rule.enabled && (
                    <span style={{
                      padding: '2px 6px',
                      backgroundColor: '#dcfce7',
                      borderRadius: '3px',
                      fontSize: '11px',
                      color: '#166534'
                    }}>
                      Enabled
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, padding: '40px', overflow: 'auto' }}>
        {selectedRule ? (
          <div>
            <h1 style={{ margin: '0 0 32px 0', fontSize: '28px', fontWeight: 'bold' }}>
              Edit Rule: {selectedRule.name}
            </h1>

            {/* Rule Form */}
            <div style={{
              backgroundColor: 'white',
              padding: '24px',
              borderRadius: '8px',
              marginBottom: '20px'
            }}>
              <div style={{ marginBottom: '20px' }}>
                <label style={{ fontSize: '14px', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
                  Rule Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
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

              <div style={{ marginBottom: '20px' }}>
                <label style={{ fontSize: '14px', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #e0e0e0',
                    borderRadius: '6px',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                    minHeight: '80px'
                  }}
                />
              </div>

              {/* Conditions Builder */}
              <div style={{ marginBottom: '20px' }}>
                <h3 style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '12px' }}>
                  Conditions
                </h3>
                
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ fontSize: '12px', color: '#666' }}>
                    Logical Operator:
                  </label>
                  <select
                    value={formData.logical_operator}
                    onChange={(e) => setFormData(prev => ({ ...prev, logical_operator: e.target.value }))}
                    style={{
                      marginLeft: '8px',
                      padding: '4px 8px',
                      border: '1px solid #e0e0e0',
                      borderRadius: '4px',
                      fontSize: '12px'
                    }}
                  >
                    <option>AND</option>
                    <option>OR</option>
                  </select>
                </div>

                {formData.conditions.map((condition, index) => (
                  <div key={index} style={{
                    display: 'flex',
                    gap: '8px',
                    marginBottom: '8px',
                    alignItems: 'center'
                  }}>
                    <input
                      type="text"
                      placeholder="Field name"
                      value={condition.field}
                      onChange={(e) => handleConditionChange(index, 'field', e.target.value)}
                      style={{
                        flex: 1,
                        padding: '6px 10px',
                        border: '1px solid #e0e0e0',
                        borderRadius: '4px',
                        fontSize: '12px'
                      }}
                    />
                    <select
                      value={condition.operator}
                      onChange={(e) => handleConditionChange(index, 'operator', e.target.value)}
                      style={{
                        padding: '6px 8px',
                        border: '1px solid #e0e0e0',
                        borderRadius: '4px',
                        fontSize: '12px'
                      }}
                    >
                      {operators.map(op => (
                        <option key={op}>{op}</option>
                      ))}
                    </select>
                    <input
                      type="text"
                      placeholder="Value"
                      value={condition.value}
                      onChange={(e) => handleConditionChange(index, 'value', e.target.value)}
                      style={{
                        flex: 1,
                        padding: '6px 10px',
                        border: '1px solid #e0e0e0',
                        borderRadius: '4px',
                        fontSize: '12px'
                      }}
                    />
                    {formData.conditions.length > 1 && (
                      <button
                        onClick={() => handleRemoveCondition(index)}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: '#fee2e2',
                          border: '1px solid #fecaca',
                          borderRadius: '4px',
                          color: '#dc2626',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        Remove
                      </button>
                    )}
                  </div>
                ))}

                <button
                  onClick={handleAddCondition}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: '#f0f0f0',
                    border: '1px solid #e0e0e0',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px',
                    marginTop: '8px'
                  }}
                >
                  + Add Condition
                </button>
              </div>

              {/* Notification Channels */}
              <div style={{ marginBottom: '20px' }}>
                <label style={{ fontSize: '14px', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
                  Notification Channels
                </label>
                <div style={{ display: 'flex', gap: '12px' }}>
                  {channels.map(channel => (
                    <label key={channel} style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={formData.notification_channels.includes(channel)}
                        onChange={() => handleChannelToggle(channel)}
                      />
                      <span style={{ fontSize: '14px', textTransform: 'capitalize' }}>{channel}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Alert Severity */}
              <div style={{ marginBottom: '20px' }}>
                <label style={{ fontSize: '14px', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
                  Alert Severity
                </label>
                <select
                  value={formData.severity}
                  onChange={(e) => setFormData(prev => ({ ...prev, severity: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #e0e0e0',
                    borderRadius: '6px',
                    fontSize: '14px',
                    boxSizing: 'border-box'
                  }}
                >
                  {severities.map(sev => (
                    <option key={sev} value={sev}>{sev.charAt(0).toUpperCase() + sev.slice(1)}</option>
                  ))}
                </select>
              </div>

              {/* Cooldown */}
              <div style={{ marginBottom: '20px' }}>
                <label style={{ fontSize: '14px', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
                  Cooldown (minutes)
                </label>
                <input
                  type="number"
                  value={formData.cooldown_minutes}
                  onChange={(e) => setFormData(prev => ({ ...prev, cooldown_minutes: parseInt(e.target.value) }))}
                  style={{
                    width: '100px',
                    padding: '8px 12px',
                    border: '1px solid #e0e0e0',
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                />
              </div>

              {/* Buttons */}
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={handleUpdateRule}
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
                  Save Changes
                </button>
                <button
                  onClick={() => setShowTestModal(true)}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: 'bold'
                  }}
                >
                  Test Rule
                </button>
                <button
                  onClick={() => handleDeleteRule(selectedRule.id)}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#ef4444',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: 'bold'
                  }}
                >
                  Delete
                </button>
              </div>
            </div>

            {/* Test Result */}
            {testResult && (
              <div style={{
                backgroundColor: 'white',
                padding: '24px',
                borderRadius: '8px',
                borderLeft: testResult.matched ? '4px solid #10b981' : '4px solid #ef4444'
              }}>
                <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 'bold' }}>
                  Test Result: {testResult.matched ? '✓ Matched' : '✗ No Match'}
                </h3>
                <pre style={{
                  backgroundColor: '#f5f5f5',
                  padding: '12px',
                  borderRadius: '4px',
                  overflow: 'auto',
                  fontSize: '12px'
                }}>
                  {JSON.stringify(testResult.details, null, 2)}
                </pre>
              </div>
            )}
          </div>
        ) : (
          <div style={{
            textAlign: 'center',
            padding: '60px 20px',
            color: '#999'
          }}>
            <p style={{ fontSize: '16px' }}>Select a rule to edit or create a new one</p>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '24px',
            maxWidth: '500px',
            maxHeight: '80vh',
            overflow: 'auto',
            boxShadow: '0 20px 25px rgba(0,0,0,0.15)'
          }}>
            <h2 style={{ margin: '0 0 20px 0', fontSize: '20px', fontWeight: 'bold' }}>
              Create New Alert Rule
            </h2>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
                Rule Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., High CPU Alert"
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #e0e0e0',
                  borderRadius: '4px',
                  fontSize: '14px',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe when this alert should trigger"
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #e0e0e0',
                  borderRadius: '4px',
                  fontSize: '14px',
                  boxSizing: 'border-box',
                  minHeight: '80px'
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '8px', marginTop: '24px' }}>
              <button
                onClick={handleCreateRule}
                style={{
                  flex: 1,
                  padding: '10px 16px',
                  backgroundColor: '#2563eb',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 'bold'
                }}
              >
                Create
              </button>
              <button
                onClick={() => { setShowCreateModal(false); resetForm(); }}
                style={{
                  flex: 1,
                  padding: '10px 16px',
                  backgroundColor: '#f0f0f0',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertManager;
