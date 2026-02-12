import React, { useState } from 'react';
import { Card, Input, Button, Spin, Alert, Tag, Row, Col, Divider, Tree } from 'antd';
import { SendOutlined, LoadingOutlined } from '@ant-design/icons';
import axios from 'axios';

const WorkflowGenerator = () => {
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [generatedWorkflow, setGeneratedWorkflow] = useState(null);
  const [error, setError] = useState('');

  const handleGenerateWorkflow = async () => {
    if (!description.trim()) {
      setError('Please enter a workflow description');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/v1/ai/workflows/generate', {
        description: description.trim(),
      });

      setGeneratedWorkflow(response.data.workflow);
      setDescription('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate workflow');
    } finally {
      setLoading(false);
    }
  };

  const renderWorkflowDAG = () => {
    if (!generatedWorkflow) return null;

    const nodes = generatedWorkflow.nodes || {};
    const edges = generatedWorkflow.edges || [];

    const treeData = Object.values(nodes).map((node) => ({
      key: node.id,
      title: (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Tag color={node.type === 'action' ? 'blue' : 'green'}>
            {node.type}
          </Tag>
          <span>{node.name}</span>
        </div>
      ),
      children: [],
    }));

    return (
      <Tree
        treeData={treeData}
        showIcon
        defaultExpandAll
      />
    );
  };

  const renderWorkflowDetails = () => {
    if (!generatedWorkflow) return null;

    const nodes = generatedWorkflow.nodes || {};
    const suggestions = generatedWorkflow.improvement_suggestions || [];

    return (
      <div style={{ marginTop: '20px' }}>
        <Card title="Generated Workflow Structure">
          <Row gutter={16} style={{ marginBottom: '20px' }}>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                  {Object.keys(nodes).length}
                </div>
                <div>Total Nodes</div>
              </div>
            </Col>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
                  {(generatedWorkflow.confidence * 100).toFixed(0)}%
                </div>
                <div>Confidence Score</div>
              </div>
            </Col>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#faad14' }}>
                  {generatedWorkflow.edges?.length || 0}
                </div>
                <div>Connections</div>
              </div>
            </Col>
          </Row>

          <Divider />

          <h4>Workflow Structure (DAG):</h4>
          <div style={{ 
            background: '#f5f5f5', 
            padding: '12px', 
            borderRadius: '4px',
            maxHeight: '300px',
            overflow: 'auto'
          }}>
            {renderWorkflowDAG()}
          </div>
        </Card>

        {suggestions.length > 0 && (
          <Card 
            title="Improvement Suggestions" 
            style={{ marginTop: '16px' }}
            type="inner"
          >
            {suggestions.map((suggestion, idx) => (
              <Alert
                key={idx}
                message={suggestion}
                type="info"
                showIcon
                style={{ marginBottom: '8px' }}
              />
            ))}
          </Card>
        )}

        <Card 
          style={{ marginTop: '16px' }}
          type="inner"
        >
          <Row gutter={16}>
            <Col span={12}>
              <Button 
                type="primary" 
                block
                onClick={() => setGeneratedWorkflow(null)}
              >
                Generate Another
              </Button>
            </Col>
            <Col span={12}>
              <Button 
                type="default" 
                block
                onClick={() => console.log('Deploy:', generatedWorkflow)}
              >
                Deploy Workflow
              </Button>
            </Col>
          </Row>
        </Card>
      </div>
    );
  };

  return (
    <div style={{ padding: '24px', background: '#fafafa', minHeight: '100vh' }}>
      <Card 
        title="🤖 AI Workflow Generator"
        style={{ maxWidth: '1200px', margin: '0 auto' }}
      >
        <p style={{ color: '#666', marginBottom: '16px' }}>
          Describe what you want to automate, and AI will generate a workflow for you.
        </p>

        <div style={{ marginBottom: '16px' }}>
          <Input.TextArea
            rows={4}
            placeholder="Describe your workflow... e.g., 'Send an email notification to users when their order is shipped, then log the event to our database'"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={loading}
          />
        </div>

        <Button
          type="primary"
          size="large"
          icon={loading ? <LoadingOutlined /> : <SendOutlined />}
          onClick={handleGenerateWorkflow}
          loading={loading}
          block
        >
          {loading ? 'Generating Workflow...' : 'Generate Workflow'}
        </Button>

        {error && (
          <Alert
            message="Error"
            description={error}
            type="error"
            closable
            onClose={() => setError('')}
            style={{ marginTop: '16px' }}
          />
        )}

        {generatedWorkflow && renderWorkflowDetails()}
      </Card>
    </div>
  );
};

export default WorkflowGenerator;
