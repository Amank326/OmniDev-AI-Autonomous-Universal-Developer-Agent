import React, { useState, useEffect } from 'react';
import { Card, Progress, Button, Space, Table, Timeline, message, Spin, Tag } from 'antd';
import { PlayCircleOutlined, StopOutlined, ReloadOutlined } from '@ant-design/icons';
import styles from './WorkflowExecutor.module.css';

/**
 * WorkflowExecutor Component
 * Displays real-time workflow execution progress with node-level tracking
 * Shows execution logs, errors, and execution history
 */
const WorkflowExecutor = ({ workflowId }) => {
  const [execution, setExecution] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [ws, setWs] = useState(null);

  useEffect(() => {
    // Connect to WebSocket for real-time updates
    const websocket = new WebSocket(`ws://localhost:8000/api/v1/phase10/ws/workflows/${workflowId}`);
    
    websocket.onopen = () => {
      console.log('Connected to workflow updates');
      websocket.send(JSON.stringify({
        type: 'subscribe',
        workflow_id: workflowId
      }));
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'execution_update') {
        setExecution(data.execution);
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    setWs(websocket);

    return () => websocket.close();
  }, [workflowId]);

  const executeWorkflow = async (inputData = {}) => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/v1/phase10/workflows/${workflowId}/execute`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(inputData)
        }
      );

      if (response.ok) {
        const data = await response.json();
        setExecution({
          id: data.execution_id,
          status: 'running',
          start_time: new Date(),
          nodeResults: {}
        });
        message.success('Workflow execution started');
        
        // Fetch execution history
        fetchExecutions();
      }
    } catch (error) {
      message.error(`Failed to execute workflow: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchExecutions = async () => {
    try {
      const response = await fetch(`/api/v1/phase10/workflows/${workflowId}/executions`);
      if (response.ok) {
        const data = await response.json();
        setExecutions(data.executions || []);
      }
    } catch (error) {
      console.error('Failed to fetch executions:', error);
    }
  };

  const stopExecution = () => {
    if (ws && execution?.id) {
      ws.send(JSON.stringify({
        type: 'cancel',
        execution_id: execution.id
      }));
      message.info('Cancellation requested');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      running: 'processing',
      success: 'success',
      failed: 'error',
      timeout: 'warning',
      cancelled: 'default'
    };
    return colors[status] || 'default';
  };

  const executionColumns = [
    {
      title: 'Execution ID',
      dataIndex: 'id',
      key: 'id',
      render: text => <code>{text.slice(0, 8)}</code>
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: status => <Tag color={getStatusColor(status)}>{status}</Tag>
    },
    {
      title: 'Duration',
      key: 'duration',
      render: (_, record) => {
        if (!record.start_time || !record.end_time) return '-';
        const duration = new Date(record.end_time) - new Date(record.start_time);
        return `${(duration / 1000).toFixed(2)}s`;
      }
    },
    {
      title: 'Started',
      dataIndex: 'start_time',
      key: 'start_time',
      render: date => new Date(date).toLocaleString()
    }
  ];

  return (
    <div className={styles.container}>
      <Card title="Workflow Executor">
        <div className={styles.controls}>
          <Space>
            <Button
              type="primary"
              size="large"
              icon={<PlayCircleOutlined />}
              onClick={() => executeWorkflow()}
              loading={loading}
            >
              Execute Workflow
            </Button>
            {execution?.status === 'running' && (
              <Button
                danger
                size="large"
                icon={<StopOutlined />}
                onClick={stopExecution}
              >
                Stop Execution
              </Button>
            )}
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchExecutions}
            >
              Refresh
            </Button>
          </Space>
        </div>

        {execution && (
          <div className={styles.executionPanel}>
            <h3>Current Execution: {execution.id.slice(0, 8)}</h3>
            
            <div className={styles.statusBox}>
              <Tag color={getStatusColor(execution.status)} style={{ fontSize: '16px' }}>
                {execution.status.toUpperCase()}
              </Tag>
            </div>

            <div className={styles.progressBox}>
              <Progress
                type="circle"
                percent={execution.status === 'success' ? 100 : execution.status === 'running' ? 50 : 0}
                status={execution.status === 'failed' ? 'exception' : undefined}
              />
            </div>

            {execution.nodeResults && Object.keys(execution.nodeResults).length > 0 && (
              <div className={styles.nodesTimeline}>
                <h4>Node Execution Timeline</h4>
                <Timeline
                  items={Object.entries(execution.nodeResults).map(([nodeId, result]) => ({
                    dot: result.status === 'success' ? undefined : undefined,
                    children: (
                      <div>
                        <strong>{nodeId}</strong>
                        <Tag color={getStatusColor(result.status)}>
                          {result.status}
                        </Tag>
                        {result.duration && <span> ({result.duration.toFixed(2)}s)</span>}
                      </div>
                    )
                  }))}
                />
              </div>
            )}

            {execution.error && (
              <div className={styles.errorBox}>
                <strong>Error:</strong> {execution.error}
              </div>
            )}
          </div>
        )}

        <div className={styles.historySection}>
          <h3>Execution History</h3>
          <Table
            columns={executionColumns}
            dataSource={executions}
            rowKey="id"
            pagination={{ pageSize: 10 }}
            size="small"
          />
        </div>
      </Card>
    </div>
  );
};

export default WorkflowExecutor;
