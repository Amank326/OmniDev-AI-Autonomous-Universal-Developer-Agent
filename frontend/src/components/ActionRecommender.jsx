import React, { useState, useEffect } from 'react';
import { Card, Button, List, Tag, Progress, Row, Col, Spin, Alert, Tooltip } from 'antd';
import { CheckCircleOutlined, WarningOutlined, BulbOutlined } from '@ant-design/icons';
import axios from 'axios';

const ActionRecommender = ({ currentAction = 'send_email' }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedRecommendation, setSelectedRecommendation] = useState(null);

  useEffect(() => {
    loadRecommendations();
  }, [currentAction]);

  const loadRecommendations = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await axios.get('/api/v1/ai/recommendations/next-actions', {
        params: {
          current_action: currentAction,
          top_k: 5,
        },
      });

      setRecommendations(response.data.recommendations || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return '#52c41a';
    if (confidence >= 0.6) return '#faad14';
    return '#f5222d';
  };

  const getSuccessProbabilityLabel = (probability) => {
    if (probability >= 0.9) return 'Very High';
    if (probability >= 0.7) return 'High';
    if (probability >= 0.5) return 'Moderate';
    return 'Low';
  };

  const renderRecommendationItem = (recommendation, index) => {
    const confidence = recommendation.confidence || 0;
    const successProb = recommendation.success_probability || 0.5;

    return (
      <Card
        key={index}
        style={{
          marginBottom: '12px',
          borderLeft: `4px solid ${getConfidenceColor(confidence)}`,
          cursor: 'pointer',
          transition: 'all 0.3s',
        }}
        onClick={() => setSelectedRecommendation(recommendation)}
        hoverable
      >
        <Row gutter={16} align="middle">
          <Col span={16}>
            <div style={{ marginBottom: '8px' }}>
              <Tag color="blue">{recommendation.action}</Tag>
              <span style={{ marginLeft: '12px', color: '#666' }}>
                {recommendation.reason}
              </span>
            </div>

            <Progress
              percent={Math.round(confidence * 100)}
              size="small"
              status={confidence >= 0.8 ? 'success' : confidence >= 0.6 ? 'normal' : 'exception'}
              strokeColor={getConfidenceColor(confidence)}
            />
          </Col>

          <Col span={8} style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '12px', color: '#999', marginBottom: '8px' }}>
              Success Rate
            </div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: getConfidenceColor(successProb) }}>
              {(successProb * 100).toFixed(0)}%
            </div>
            <div style={{ fontSize: '11px', color: '#666' }}>
              {getSuccessProbabilityLabel(successProb)}
            </div>
          </Col>
        </Row>

        {recommendation.estimated_duration > 0 && (
          <div style={{ marginTop: '8px', fontSize: '12px', color: '#999' }}>
            ⏱️ Est. Duration: {recommendation.estimated_duration.toFixed(1)}s
          </div>
        )}
      </Card>
    );
  };

  const renderDetailedView = () => {
    if (!selectedRecommendation) return null;

    return (
      <Card
        title="Action Details"
        style={{ marginTop: '16px' }}
        extra={
          <Button
            type="text"
            onClick={() => setSelectedRecommendation(null)}
          >
            ✕
          </Button>
        }
      >
        <Row gutter={16}>
          <Col span={12}>
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '12px', color: '#999', marginBottom: '4px' }}>
                ACTION
              </div>
              <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                {selectedRecommendation.action}
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '12px', color: '#999', marginBottom: '4px' }}>
                RECOMMENDATION REASON
              </div>
              <div style={{ fontSize: '14px' }}>
                {selectedRecommendation.reason}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '12px', color: '#999', marginBottom: '4px' }}>
                SUCCESS EXPLANATION
              </div>
              <div style={{ fontSize: '14px' }}>
                {selectedRecommendation.success_explanation}
              </div>
            </div>
          </Col>

          <Col span={12}>
            <div style={{ background: '#f5f5f5', padding: '16px', borderRadius: '4px' }}>
              <Row gutter={16}>
                <Col span={12}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                      {(selectedRecommendation.confidence * 100).toFixed(0)}%
                    </div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      Confidence Score
                    </div>
                  </div>
                </Col>
                <Col span={12}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
                      {(selectedRecommendation.success_probability * 100).toFixed(0)}%
                    </div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      Success Probability
                    </div>
                  </div>
                </Col>
              </Row>

              {selectedRecommendation.estimated_duration > 0 && (
                <div style={{ marginTop: '16px', textAlign: 'center' }}>
                  <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                    Estimated Duration
                  </div>
                  <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
                    {selectedRecommendation.estimated_duration.toFixed(1)}s
                  </div>
                </div>
              )}
            </div>

            <Button
              type="primary"
              block
              style={{ marginTop: '16px' }}
              icon={<CheckCircleOutlined />}
              onClick={() => {
                console.log('Selected action:', selectedRecommendation.action);
                setSelectedRecommendation(null);
              }}
            >
              Use This Action
            </Button>
          </Col>
        </Row>
      </Card>
    );
  };

  return (
    <div style={{ padding: '24px', background: '#fafafa', minHeight: '100vh' }}>
      <Card
        title="💡 AI Action Recommender"
        style={{ maxWidth: '1000px', margin: '0 auto' }}
      >
        <p style={{ color: '#666', marginBottom: '16px' }}>
          Intelligent recommendations for the next action in your workflow based on execution history and success patterns.
        </p>

        <div style={{ marginBottom: '16px' }}>
          <span style={{ fontSize: '14px', fontWeight: 'bold', color: '#333' }}>
            Current Action:
          </span>
          <Tag color="blue" style={{ marginLeft: '8px' }}>
            {currentAction}
          </Tag>
        </div>

        {error && (
          <Alert
            message="Error"
            description={error}
            type="error"
            closable
            onClose={() => setError('')}
            style={{ marginBottom: '16px' }}
          />
        )}

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" />
          </div>
        ) : recommendations.length > 0 ? (
          <div>
            <div style={{ marginBottom: '16px' }}>
              <span style={{ fontSize: '12px', color: '#999' }}>
                {recommendations.length} recommendations available
              </span>
            </div>

            <div>
              {recommendations.map((rec, idx) => renderRecommendationItem(rec, idx))}
            </div>
          </div>
        ) : (
          <Alert
            message="No recommendations available"
            description="Not enough execution history to provide recommendations."
            type="info"
            icon={<BulbOutlined />}
          />
        )}

        {renderDetailedView()}

        <Button
          type="dashed"
          block
          style={{ marginTop: '16px' }}
          onClick={loadRecommendations}
        >
          Refresh Recommendations
        </Button>
      </Card>
    </div>
  );
};

export default ActionRecommender;
