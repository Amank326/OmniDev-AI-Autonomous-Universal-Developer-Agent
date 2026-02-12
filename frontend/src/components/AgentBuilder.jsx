import React, { useState, useEffect } from 'react';
import {
  Plus, Trash2, Settings, Play, Save, Code, Copy, Send,
  AlertCircle, CheckCircle, Clock, DollarSign
} from 'lucide-react';
import '../styles/agent-builder.css';

const AgentBuilder = () => {
  const [workflows, setWorkflows] = useState([]);
  const [deployments, setDeployments] = useState([]);
  
  // Workflow Editor
  const [currentWorkflow, setCurrentWorkflow] = useState(null);
  const [workflowName, setWorkflowName] = useState('');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [agents, setAgents] = useState([]);
  const [selectedAgents, setSelectedAgents] = useState([]);
  
  // Execution
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [executionError, setExecutionError] = useState(null);
  const [testInput, setTestInput] = useState('');
  
  // UI State
  const [showNewWorkflow, setShowNewWorkflow] = useState(false);
  const [showDeployment, setShowDeployment] = useState(false);
  const [selectedDeployment, setSelectedDeployment] = useState(null);

  useEffect(() => {
    fetchWorkflows();
    fetchDeployments();
    fetchAvailableAgents();
  }, []);

  const fetchWorkflows = async () => {
    try {
      const response = await fetch('/api/v1/agents/workflows', {
        headers: { 'X-User-ID': 'current-user' }
      });
      const data = await response.json();
      setWorkflows(data.workflows || []);
    } catch (error) {
      console.error('Error fetching workflows:', error);
    }
  };

  const fetchDeployments = async () => {
    try {
      const response = await fetch('/api/v1/agents/deployments', {
        headers: { 'X-User-ID': 'current-user' }
      });
      const data = await response.json();
      setDeployments(data.deployments || []);
    } catch (error) {
      console.error('Error fetching deployments:', error);
    }
  };

  const fetchAvailableAgents = async () => {
    try {
      const response = await fetch('/api/v1/agents/search?limit=100');
      const data = await response.json();
      setAgents(data.agents || []);
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  };

  const createWorkflow = async () => {
    if (!workflowName.trim()) {
      alert('Workflow name is required');
      return;
    }

    if (selectedAgents.length === 0) {
      alert('Add at least one agent to the workflow');
      return;
    }

    try {
      const response = await fetch('/api/v1/agents/workflows', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': 'current-user'
        },
        body: JSON.stringify({
          name: workflowName,
          description: workflowDescription,
          agents: selectedAgents.map((id, idx) => ({
            agent_id: id,
            config: {},
            step_number: idx + 1
          })),
          routing: []
        })
      });

      const data = await response.json();
      setCurrentWorkflow(data);
      setWorkflowName('');
      setWorkflowDescription('');
      setSelectedAgents([]);
      setShowNewWorkflow(false);
      fetchWorkflows();
    } catch (error) {
      console.error('Error creating workflow:', error);
    }
  };

  const addAgentToWorkflow = (agentId) => {
    if (!selectedAgents.includes(agentId)) {
      setSelectedAgents([...selectedAgents, agentId]);
    }
  };

  const removeAgentFromWorkflow = (index) => {
    setSelectedAgents(selectedAgents.filter((_, i) => i !== index));
  };

  const reorderAgents = (fromIndex, toIndex) => {
    const newAgents = [...selectedAgents];
    const [agent] = newAgents.splice(fromIndex, 1);
    newAgents.splice(toIndex, 0, agent);
    setSelectedAgents(newAgents);
  };

  const executeWorkflow = async () => {
    if (!currentWorkflow) return;

    setIsExecuting(true);
    setExecutionError(null);
    setExecutionResult(null);

    try {
      const response = await fetch(
        `/api/v1/agents/workflows/${currentWorkflow.workflow_id}/execute`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-User-ID': 'current-user'
          },
          body: JSON.stringify({
            input: testInput || 'Execute workflow',
            context: {}
          })
        }
      );

      const data = await response.json();
      
      // Poll for execution result
      let maxAttempts = 30;
      while (maxAttempts-- > 0) {
        const statusResponse = await fetch(`/api/v1/agents/executions/${data.execution_id}`);
        const statusData = await statusResponse.json();

        if (statusData.status === 'completed') {
          setExecutionResult(statusData);
          break;
        } else if (statusData.status === 'failed') {
          setExecutionError(statusData.error);
          break;
        }

        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    } catch (error) {
      setExecutionError(error.message);
    } finally {
      setIsExecuting(false);
    }
  };

  const WorkflowCanvas = () => {
    if (!currentWorkflow && !showNewWorkflow) {
      return (
        <div className="canvas-empty-state">
          <h3>Create a Workflow</h3>
          <p>Build agent chains to automate complex tasks</p>
          <button onClick={() => setShowNewWorkflow(true)} className="btn-primary">
            <Plus size={20} /> New Workflow
          </button>
        </div>
      );
    }

    return (
      <div className="workflow-canvas">
        <div className="canvas-header">
          <input
            type="text"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            placeholder="Workflow name"
            className="workflow-name-input"
          />
          <button onClick={createWorkflow} className="btn-save">
            <Save size={18} /> Save Workflow
          </button>
        </div>

        <div className="canvas-content">
          {/* Agent Selection */}
          <div className="agent-selector">
            <h4>Add Agents</h4>
            <div className="agent-search">
              <input type="text" placeholder="Search agents..." />
            </div>
            <div className="available-agents">
              {agents.map(agent => (
                <div
                  key={agent.id}
                  className="agent-option"
                  onClick={() => addAgentToWorkflow(agent.id)}
                >
                  <span>{agent.name}</span>
                  <Plus size={16} />
                </div>
              ))}
            </div>
          </div>

          {/* Workflow Builder */}
          <div className="workflow-builder">
            <h4>Workflow Steps</h4>
            <div className="steps-container">
              {selectedAgents.length === 0 ? (
                <p className="no-agents">Add agents from the left panel</p>
              ) : (
                selectedAgents.map((agentId, index) => {
                  const agent = agents.find(a => a.id === agentId);
                  return (
                    <div key={index} className="workflow-step">
                      <div className="step-number">{index + 1}</div>
                      <div className="step-content">
                        <h5>{agent?.name || 'Unknown Agent'}</h5>
                        <p className="step-description">{agent?.description}</p>
                      </div>
                      <div className="step-actions">
                        <button
                          onClick={() => removeAgentFromWorkflow(index)}
                          className="btn-remove"
                          title="Remove"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                      {index < selectedAgents.length - 1 && (
                        <div className="step-connector">↓</div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Test Execution */}
        {selectedAgents.length > 0 && (
          <div className="test-section">
            <h4>Test Workflow</h4>
            <textarea
              value={testInput}
              onChange={(e) => setTestInput(e.target.value)}
              placeholder="Enter test input for the first agent..."
              className="test-input"
              rows={4}
            />

            <button
              onClick={executeWorkflow}
              disabled={isExecuting}
              className="btn-execute"
            >
              <Play size={18} />
              {isExecuting ? 'Executing...' : 'Test Workflow'}
            </button>

            {executionError && (
              <div className="execution-error">
                <AlertCircle size={20} />
                <p>{executionError}</p>
              </div>
            )}

            {executionResult && (
              <div className="execution-result">
                <div className="result-header">
                  <CheckCircle size={20} className="success-icon" />
                  <h5>Execution Successful</h5>
                </div>
                <div className="result-output">
                  <pre>{JSON.stringify(executionResult.output, null, 2)}</pre>
                </div>
                <div className="result-meta">
                  <span className="duration">
                    <Clock size={14} />
                    {executionResult.ended_at
                      ? new Date(executionResult.ended_at).getTime() -
                        new Date(executionResult.started_at).getTime()
                      : 0}
                    ms
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const DeploymentManager = () => (
    <div className="deployment-manager">
      <div className="deployments-header">
        <h3>Active Deployments</h3>
        {currentWorkflow && (
          <button onClick={() => setShowDeployment(true)} className="btn-primary">
            <Plus size={18} /> Deploy Workflow
          </button>
        )}
      </div>

      {deployments.length === 0 ? (
        <div className="no-deployments">
          <p>No active deployments</p>
          <p className="hint">Create a workflow and deploy it to get started</p>
        </div>
      ) : (
        <div className="deployments-list">
          {deployments.map(deployment => (
            <div
              key={deployment.id}
              className="deployment-card"
              onClick={() => setSelectedDeployment(deployment)}
            >
              <div className="deployment-info">
                <h4>{deployment.name}</h4>
                <p className="deployment-meta">
                  Environment: <strong>{deployment.environment}</strong>
                </p>
                <p className="deployment-created">
                  Created {new Date(deployment.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="deployment-status">
                <span className={`status-badge ${deployment.is_active ? 'active' : 'inactive'}`}>
                  {deployment.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedDeployment && (
        <div className="deployment-details">
          <h4>{selectedDeployment.name}</h4>
          <div className="details-grid">
            <div className="detail-item">
              <label>Environment</label>
              <span>{selectedDeployment.environment}</span>
            </div>
            <div className="detail-item">
              <label>Status</label>
              <span className="status-badge">{selectedDeployment.is_active ? 'Active' : 'Inactive'}</span>
            </div>
            <div className="detail-item">
              <label>Created</label>
              <span>{new Date(selectedDeployment.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="agent-builder">
      <header className="builder-header">
        <h1>Agent Workflow Builder</h1>
        <p>Create and manage AI agent workflows</p>
      </header>

      <div className="builder-layout">
        <aside className="sidebar">
          <div className="sidebar-section">
            <h3>My Workflows</h3>
            <div className="workflows-list">
              {workflows.map(workflow => (
                <button
                  key={workflow.id}
                  className={`workflow-item ${currentWorkflow?.id === workflow.id ? 'active' : ''}`}
                  onClick={() => setCurrentWorkflow(workflow)}
                >
                  {workflow.name}
                </button>
              ))}
            </div>
            <button onClick={() => setShowNewWorkflow(true)} className="btn-new">
              <Plus size={18} /> New Workflow
            </button>
          </div>

          <div className="sidebar-section">
            <h3>Quick Access</h3>
            <button className="quick-access-item">
              <Settings size={18} /> Agent Settings
            </button>
            <button className="quick-access-item">
              <Code size={18} /> API Documentation
            </button>
          </div>
        </aside>

        <main className="main-content">
          <WorkflowCanvas />
        </main>

        <aside className="right-sidebar">
          <DeploymentManager />
        </aside>
      </div>
    </div>
  );
};

export default AgentBuilder;
