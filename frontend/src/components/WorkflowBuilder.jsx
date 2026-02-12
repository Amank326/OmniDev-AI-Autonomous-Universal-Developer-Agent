import React, { useState, useCallback } from 'react';
import { Card, Button, Form, Input, Select, Space, Tree, Modal, message } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons';
import styles from './WorkflowBuilder.module.css';

/**
 * WorkflowBuilder Component
 * Drag-and-drop visual workflow editor with node management
 * Supports creating DAG workflows with sequential, parallel, and conditional execution
 */
const WorkflowBuilder = () => {
  const [workflow, setWorkflow] = useState({
    name: 'New Workflow',
    nodes: {},
    edges: [],
    variables: {}
  });

  const [selectedNode, setSelectedNode] = useState(null);
  const [showNodeModal, setShowNodeModal] = useState(false);
  const [nodeForm] = Form.useForm();

  // Node types available
  const nodeTypes = [
    { label: 'Start', value: 'start' },
    { label: 'Action', value: 'action' },
    { label: 'Decision', value: 'decision' },
    { label: 'Parallel', value: 'parallel' },
    { label: 'Wait', value: 'wait' },
    { label: 'End', value: 'end' }
  ];

  const actionTypes = [
    { label: 'Send Email', value: 'send_email' },
    { label: 'Send Slack', value: 'send_slack' },
    { label: 'Create Record', value: 'create_record' },
    { label: 'Update Record', value: 'update_record' },
    { label: 'Query Data', value: 'query_data' },
    { label: 'Call API', value: 'call_api' },
    { label: 'Trigger Workflow', value: 'trigger_workflow' },
    { label: 'Log Event', value: 'log_event' }
  ];

  const addNode = () => {
    const nodeId = `node_${Date.now()}`;
    setSelectedNode(nodeId);
    setWorkflow(prev => ({
      ...prev,
      nodes: {
        ...prev.nodes,
        [nodeId]: {
          id: nodeId,
          name: 'New Node',
          type: 'action',
          config: {}
        }
      }
    }));
    setShowNodeModal(true);
  };

  const updateNode = (nodeId, updates) => {
    setWorkflow(prev => ({
      ...prev,
      nodes: {
        ...prev.nodes,
        [nodeId]: {
          ...prev.nodes[nodeId],
          ...updates
        }
      }
    }));
  };

  const deleteNode = (nodeId) => {
    setWorkflow(prev => {
      const newWorkflow = { ...prev };
      delete newWorkflow.nodes[nodeId];
      // Remove edges connected to this node
      newWorkflow.edges = newWorkflow.edges.filter(
        e => e.source !== nodeId && e.target !== nodeId
      );
      return newWorkflow;
    });
    message.success('Node deleted');
  };

  const addEdge = (sourceId, targetId) => {
    if (sourceId === targetId) {
      message.error('Cannot connect node to itself');
      return;
    }

    setWorkflow(prev => ({
      ...prev,
      edges: [...prev.edges, { source: sourceId, target: targetId }]
    }));
    message.success('Edge created');
  };

  const saveWorkflow = async () => {
    try {
      const response = await fetch('/api/v1/phase10/workflows/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(workflow)
      });

      if (response.ok) {
        const data = await response.json();
        message.success(`Workflow saved: ${data.workflow_id}`);
      }
    } catch (error) {
      message.error(`Failed to save workflow: ${error.message}`);
    }
  };

  const renderNodes = () => {
    return Object.entries(workflow.nodes).map(([nodeId, node]) => (
      <div key={nodeId} className={styles.nodeBox}>
        <div className={styles.nodeHeader}>
          <span className={styles.nodeType}>{node.type}</span>
          <Space>
            <Button
              size="small"
              type="text"
              icon={<EditOutlined />}
              onClick={() => {
                setSelectedNode(nodeId);
                setShowNodeModal(true);
              }}
            />
            <Button
              size="small"
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => deleteNode(nodeId)}
            />
          </Space>
        </div>
        <div className={styles.nodeName}>{node.name}</div>
        {node.action_type && (
          <div className={styles.nodeAction}>{node.action_type}</div>
        )}
      </div>
    ));
  };

  const renderEdges = () => {
    return workflow.edges.map((edge, idx) => (
      <div key={idx} className={styles.edge}>
        {workflow.nodes[edge.source]?.name} → {workflow.nodes[edge.target]?.name}
        <Button
          size="small"
          type="text"
          danger
          onClick={() => {
            setWorkflow(prev => ({
              ...prev,
              edges: prev.edges.filter((_, i) => i !== idx)
            }));
          }}
        >
          Remove
        </Button>
      </div>
    ));
  };

  return (
    <div className={styles.container}>
      <Card title="Workflow Builder" extra={
        <Button type="primary" icon={<SaveOutlined />} onClick={saveWorkflow}>
          Save Workflow
        </Button>
      }>
        <div className={styles.controls}>
          <Form layout="inline">
            <Form.Item label="Workflow Name">
              <Input
                value={workflow.name}
                onChange={e => setWorkflow(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Enter workflow name"
                style={{ width: '300px' }}
              />
            </Form.Item>
            <Form.Item>
              <Button type="primary" icon={<PlusOutlined />} onClick={addNode}>
                Add Node
              </Button>
            </Form.Item>
          </Form>
        </div>

        <div className={styles.canvas}>
          <div className={styles.nodesSection}>
            <h3>Nodes ({Object.keys(workflow.nodes).length})</h3>
            {renderNodes()}
          </div>

          <div className={styles.edgesSection}>
            <h3>Connections ({workflow.edges.length})</h3>
            {renderEdges()}
          </div>
        </div>
      </Card>

      <Modal
        title={`Edit Node: ${selectedNode}`}
        open={showNodeModal}
        onOk={() => {
          if (selectedNode) {
            const values = nodeForm.getFieldsValue();
            updateNode(selectedNode, values);
            setShowNodeModal(false);
          }
        }}
        onCancel={() => setShowNodeModal(false)}
      >
        <Form
          form={nodeForm}
          layout="vertical"
          initialValues={workflow.nodes[selectedNode]}
        >
          <Form.Item label="Node Name" name="name">
            <Input placeholder="Node name" />
          </Form.Item>

          <Form.Item label="Node Type" name="type">
            <Select options={nodeTypes} />
          </Form.Item>

          {workflow.nodes[selectedNode]?.type === 'action' && (
            <Form.Item label="Action Type" name="action_type">
              <Select options={actionTypes} />
            </Form.Item>
          )}

          {workflow.nodes[selectedNode]?.type === 'wait' && (
            <Form.Item label="Duration (seconds)" name={['config', 'duration']}>
              <Input type="number" placeholder="300" />
            </Form.Item>
          )}

          {workflow.nodes[selectedNode]?.type === 'decision' && (
            <Form.Item label="Condition" name={['config', 'condition']}>
              <Input.TextArea placeholder="value > 100" rows={3} />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default WorkflowBuilder;
