/**
 * Agent Orchestration Dashboard Component
 * Real-time monitoring and management of multi-agent orchestration
 */

import React, { useState, useEffect, useCallback } from 'react';
import io from 'socket.io-client';
import './AgentOrchestrationDashboard.css';

// Status badge component
const StatusBadge = ({ status, type = 'agent' }) => {
  const statusColors = {
    agent: {
      idle: '#10b981',
      busy: '#f59e0b',
      processing: '#3b82f6',
      waiting: '#8b5cf6',
      error: '#ef4444',
      offline: '#6b7280',
      maintenance: '#ec4899',
    },
    task: {
      pending: '#9ca3af',
      queued: '#3b82f6',
      running: '#f59e0b',
      paused: '#8b5cf6',
      completed: '#10b981',
      failed: '#ef4444',
      cancelled: '#6b7280',
      blocked: '#ec4899',
    },
  };

  const color = statusColors[type][status] || '#9ca3af';

  return (
    <span
      className="status-badge"
      style={{ backgroundColor: color, color: 'white', padding: '4px 12px', borderRadius: '12px', fontSize: '12px', fontWeight: '500' }}
    >
      {status.toUpperCase()}
    </span>
  );
};

// Agent Card Component
const AgentCard = ({ agent, onSelect }) => {
  const loadColor = agent.load_percent > 80 ? '#ef4444' : agent.load_percent > 50 ? '#f59e0b' : '#10b981';

  return (
    <div
      className="agent-card"
      onClick={() => onSelect(agent.id)}
      style={{
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '12px',
        cursor: 'pointer',
        transition: 'all 0.2s',
        ':hover': { boxShadow: '0 4px 12px rgba(0,0,0,0.1)' },
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
        <div>
          <h3 style={{ margin: '0 0 4px 0', fontSize: '16px', fontWeight: '600' }}>{agent.name}</h3>
          <p style={{ margin: '0', fontSize: '12px', color: '#6b7280' }}>ID: {agent.id.substring(0, 8)}...</p>
        </div>
        <StatusBadge status={agent.status} type="agent" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px', fontSize: '12px' }}>
        <div style={{ backgroundColor: '#f3f4f6', padding: '8px', borderRadius: '4px' }}>
          <span style={{ color: '#6b7280' }}>Load:</span>
          <p style={{ margin: '4px 0 0 0', fontSize: '14px', fontWeight: '600' }}>
            {agent.load_percent ? agent.load_percent.toFixed(1) : 0}%
          </p>
        </div>
        <div style={{ backgroundColor: '#f3f4f6', padding: '8px', borderRadius: '4px' }}>
          <span style={{ color: '#6b7280' }}>Tasks:</span>
          <p style={{ margin: '4px 0 0 0', fontSize: '14px', fontWeight: '600' }}>
            {agent.current_tasks}/{agent.max_concurrent_tasks}
          </p>
        </div>
      </div>

      <div style={{ width: '100%', height: '6px', backgroundColor: '#e5e7eb', borderRadius: '3px', overflow: 'hidden' }}>
        <div
          style={{
            width: `${agent.load_percent || 0}%`,
            height: '100%',
            backgroundColor: loadColor,
            transition: 'width 0.3s',
          }}
        />
      </div>

      <div style={{ marginTop: '12px', fontSize: '11px', color: '#6b7280' }}>
        Memory: {agent.memory_max_mb - agent.memory_available_mb}/{agent.memory_max_mb} MB
      </div>
    </div>
  );
};

// Task Queue Component
const TaskQueueView = ({ agentId, tasks, onTaskSelect }) => {
  return (
    <div style={{ marginTop: '20px' }}>
      <h3 style={{ marginTop: '0', marginBottom: '12px', fontSize: '14px', fontWeight: '600' }}>
        Task Queue ({tasks.length})
      </h3>

      <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {tasks.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af', fontSize: '12px' }}>
            No tasks in queue
          </div>
        ) : (
          tasks.map((task) => (
            <div
              key={task.id}
              onClick={() => onTaskSelect(task.id)}
              style={{
                padding: '12px',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                marginBottom: '8px',
                backgroundColor: '#f9fafb',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '8px' }}>
                <div>
                  <p style={{ margin: '0', fontSize: '13px', fontWeight: '500' }}>{task.name}</p>
                  <p style={{ margin: '4px 0 0 0', fontSize: '11px', color: '#6b7280' }}>
                    {task.id.substring(0, 12)}...
                  </p>
                </div>
                <StatusBadge status={task.status} type="task" />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '11px' }}>
                <span>Priority: <strong>{task.priority}</strong></span>
                <span>Type: <strong>{task.type}</strong></span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// System Health Component
const SystemHealth = ({ health }) => {
  return (
    <div
      style={{
        backgroundColor: '#f9fafb',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        padding: '16px',
        marginTop: '20px',
      }}
    >
      <h3 style={{ marginTop: '0', marginBottom: '16px', fontSize: '14px', fontWeight: '600' }}>
        System Health
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px' }}>
        <div style={{ backgroundColor: 'white', padding: '12px', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
          <p style={{ margin: '0', fontSize: '11px', color: '#6b7280' }}>Total Agents</p>
          <p style={{ margin: '4px 0 0 0', fontSize: '18px', fontWeight: '700', color: '#1f2937' }}>
            {health.total_agents || 0}
          </p>
        </div>

        <div style={{ backgroundColor: 'white', padding: '12px', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
          <p style={{ margin: '0', fontSize: '11px', color: '#6b7280' }}>Active Agents</p>
          <p style={{ margin: '4px 0 0 0', fontSize: '18px', fontWeight: '700', color: '#10b981' }}>
            {health.active_agents || 0}
          </p>
        </div>

        <div style={{ backgroundColor: 'white', padding: '12px', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
          <p style={{ margin: '0', fontSize: '11px', color: '#6b7280' }}>Running Tasks</p>
          <p style={{ margin: '4px 0 0 0', fontSize: '18px', fontWeight: '700', color: '#3b82f6' }}>
            {health.total_tasks_running || 0}
          </p>
        </div>

        <div style={{ backgroundColor: 'white', padding: '12px', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
          <p style={{ margin: '0', fontSize: '11px', color: '#6b7280' }}>Avg Success Rate</p>
          <p style={{ margin: '4px 0 0 0', fontSize: '18px', fontWeight: '700', color: '#10b981' }}>
            {health.avg_success_rate ? health.avg_success_rate.toFixed(1) : 100}%
          </p>
        </div>

        <div style={{ backgroundColor: 'white', padding: '12px', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
          <p style={{ margin: '0', fontSize: '11px', color: '#6b7280' }}>System Load</p>
          <p style={{ margin: '4px 0 0 0', fontSize: '18px', fontWeight: '700', color: '#f59e0b' }}>
            {health.total_load_percent ? health.total_load_percent.toFixed(1) : 0}%
          </p>
        </div>

        <div style={{ backgroundColor: 'white', padding: '12px', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
          <p style={{ margin: '0', fontSize: '11px', color: '#6b7280' }}>Memory Usage</p>
          <p style={{ margin: '4px 0 0 0', fontSize: '18px', fontWeight: '700', color: '#8b5cf6' }}>
            {health.memory_usage_percent ? health.memory_usage_percent.toFixed(1) : 0}%
          </p>
        </div>
      </div>
    </div>
  );
};

// Main Dashboard Component
const AgentOrchestrationDashboard = () => {
  const [agents, setAgents] = useState([]);
  const [selectedAgentId, setSelectedAgentId] = useState(null);
  const [systemHealth, setSystemHealth] = useState({});
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000';

  // Initialize WebSocket
  useEffect(() => {
    const newSocket = io(`${apiUrl}/orchestration`, {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5,
      query: {
        user_id: localStorage.getItem('userId') || 'dashboard-user',
      },
    });

    newSocket.on('connect', () => {
      setIsConnected(true);
      console.log('Connected to orchestration WebSocket');
    });

    newSocket.on('disconnect', () => {
      setIsConnected(false);
    });

    newSocket.on('system_stats', (data) => {
      setSystemHealth(data.system || {});
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, [apiUrl]);

  // Fetch agents
  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/v1/orchestration/agents`);
        const data = await response.json();
        if (data.success && data.data) {
          setAgents(Object.values(data.data));
        }
      } catch (error) {
        console.error('Error fetching agents:', error);
      }
    };

    fetchAgents();
    const interval = setInterval(fetchAgents, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, [apiUrl]);

  // Fetch system health periodically
  useEffect(() => {
    if (socket && isConnected) {
      const interval = setInterval(() => {
        socket.emit('request_system_stats', { workspace_id: 'default' });
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [socket, isConnected]);

  // Get selected agent details
  const selectedAgent = agents.find((a) => a.id === selectedAgentId);
  const agentQueue = selectedAgent ? [] : []; // Would fetch from API

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <h1 style={{ margin: '0', fontSize: '28px', fontWeight: '700' }}>
            🚀 Agent Orchestration Dashboard
          </h1>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              backgroundColor: isConnected ? '#10b981' : '#6b7280',
              color: 'white',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: '500',
            }}
          >
            <span style={{ width: '8px', height: '8px', backgroundColor: 'white', borderRadius: '50%', display: 'inline-block' }} />
            {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
          </div>
        </div>
        <p style={{ margin: '0', color: '#6b7280', fontSize: '14px' }}>
          Monitor and manage multi-agent orchestration in real-time
        </p>
      </div>

      {/* Main Content */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedAgentId ? '1fr 1fr' : '1fr', gap: '24px' }}>
        {/* Left Panel - Agents List */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ margin: '0', fontSize: '16px', fontWeight: '600' }}>Agents ({agents.length})</h2>
            <button
              onClick={() => setSelectedAgentId(null)}
              style={{
                padding: '6px 12px',
                backgroundColor: '#f3f4f6',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                fontSize: '12px',
                cursor: 'pointer',
              }}
            >
              Clear Selection
            </button>
          </div>

          <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
            {agents.length === 0 ? (
              <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af' }}>
                No agents available
              </div>
            ) : (
              agents.map((agent) => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  onSelect={setSelectedAgentId}
                />
              ))
            )}
          </div>
        </div>

        {/* Right Panel - Selected Agent Details */}
        {selectedAgent && (
          <div>
            <div
              style={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '20px',
              }}
            >
              <h2 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600' }}>
                {selectedAgent.name}
              </h2>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '12px',
                  marginBottom: '20px',
                  fontSize: '13px',
                }}
              >
                <div>
                  <span style={{ color: '#6b7280' }}>Status:</span>
                  <p style={{ margin: '4px 0 0 0' }}>
                    <StatusBadge status={selectedAgent.status} type="agent" />
                  </p>
                </div>

                <div>
                  <span style={{ color: '#6b7280' }}>Type:</span>
                  <p style={{ margin: '4px 0 0 0', fontWeight: '500' }}>{selectedAgent.type}</p>
                </div>

                <div>
                  <span style={{ color: '#6b7280' }}>Success Rate:</span>
                  <p style={{ margin: '4px 0 0 0', fontWeight: '500' }}>
                    {selectedAgent.metrics.success_rate.toFixed(1)}%
                  </p>
                </div>

                <div>
                  <span style={{ color: '#6b7280' }}>Tasks Completed:</span>
                  <p style={{ margin: '4px 0 0 0', fontWeight: '500' }}>
                    {selectedAgent.metrics.total_tasks_completed}
                  </p>
                </div>

                <div>
                  <span style={{ color: '#6b7280' }}>Capabilities:</span>
                  <p style={{ margin: '4px 0 0 0', fontWeight: '500' }}>
                    {selectedAgent.capabilities.join(', ')}
                  </p>
                </div>

                <div>
                  <span style={{ color: '#6b7280' }}>Last Heartbeat:</span>
                  <p style={{ margin: '4px 0 0 0', fontWeight: '500' }}>
                    {selectedAgent.last_heartbeat
                      ? new Date(selectedAgent.last_heartbeat).toLocaleTimeString()
                      : 'Never'}
                  </p>
                </div>
              </div>

              {/* Task Queue */}
              <TaskQueueView
                agentId={selectedAgent.id}
                tasks={agentQueue}
                onTaskSelect={(taskId) => console.log('Selected task:', taskId)}
              />
            </div>
          </div>
        )}
      </div>

      {/* System Health */}
      <SystemHealth health={systemHealth} />
    </div>
  );
};

export default AgentOrchestrationDashboard;
