"""
RecommendationCard Component

Displays personalized AI recommendations with:
- Recommendation details
- Confidence scores
- Impact estimates
- CTR metrics
- A/B test variants
"""

import React, { useState } from 'react';
import { Card, Button, Progress, Tag, Row, Col, Statistic, Rate } from 'antd';
import { ArrowRightOutlined, CheckOutlined, ExperimentOutlined } from '@ant-design/icons';
import axios from 'axios';

const RecommendationCard = ({ 
  recommendation, 
  onAction = null,
  showMetrics = true 
}) => {
  const [tracked, setTracked] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleAction = async (actionType = 'clicked') => {
    setLoading(true);
    try {
      await axios.post(
        `/api/v1/phase9/recommendations/${recommendation.recommendation_id}/track`,
        {
          action_taken: actionType === 'clicked',
          conversion: actionType === 'converted'
        },
        {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        }
      );
      setTracked(true);
      onAction?.({
        recommendation_id: recommendation.recommendation_id,
        action: actionType
      });
    } catch (error) {
      console.error('Error tracking recommendation:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      retention: 'red',
      engagement: 'blue',
      education: 'cyan',
      community: 'purple',
      upsell: 'gold',
      addon: 'green',
      adoption: 'orange',
      support: 'magenta',
      feature: 'lime'
    };
    return colors[category] || 'blue';
  };

  const getImpactColor = (impact) => {
    if (impact > 0.5) return 'green';
    if (impact > 0.3) return 'orange';
    return 'blue';
  };

  return (
    <Card
      style={{
        marginBottom: '16px',
        border: tracked ? '2px solid #52c41a' : '1px solid #d9d9d9'
      }}
    >
      <Row gutter={[16, 16]} align="top">
        {/* Main Content */}
        <Col xs={24} md={16}>
          <div style={{ marginBottom: '12px' }}>
            <Tag color={getCategoryColor(recommendation.category)}>
              {recommendation.category?.toUpperCase()}
            </Tag>
            {recommendation.ab_test_variant && (
              <Tag icon={<ExperimentOutlined />} style={{ marginLeft: '8px' }}>
                {recommendation.ab_test_variant.toUpperCase()}
              </Tag>
            )}
          </div>

          <h3 style={{ marginBottom: '8px' }}>
            {recommendation.title}
          </h3>

          <p style={{ color: '#666', marginBottom: '12px' }}>
            {recommendation.description}
          </p>

          {recommendation.explanation && (
            <p style={{ 
              fontSize: '12px', 
              color: '#999',
              backgroundColor: '#fafafa',
              padding: '8px',
              borderRadius: '4px',
              marginBottom: '12px'
            }}>
              <strong>Why:</strong> {recommendation.explanation}
            </p>
          )}

          {/* Action Button */}
          <Button
            type="primary"
            size="large"
            onClick={() => handleAction('clicked')}
            disabled={tracked || loading}
            loading={loading}
            icon={<ArrowRightOutlined />}
          >
            {tracked ? <CheckOutlined /> : null}
            {tracked ? 'Action Recorded' : 'Take Action'}
          </Button>

          {recommendation.action_url && !tracked && (
            <Button
              type="link"
              size="small"
              style={{ marginLeft: '8px' }}
              href={recommendation.action_url}
              target="_blank"
            >
              View Details
            </Button>
          )}
        </Col>

        {/* Metrics */}
        <Col xs={24} md={8}>
          <div style={{
            backgroundColor: '#fafafa',
            padding: '12px',
            borderRadius: '4px'
          }}>
            {/* Confidence */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                Confidence
              </div>
              <Progress
                percent={Math.round(recommendation.confidence * 100)}
                size="small"
                status={recommendation.confidence > 0.75 ? 'success' : 'normal'}
              />
            </div>

            {/* Impact */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                Estimated Impact
              </div>
              <Progress
                percent={Math.round(recommendation.impact * 100)}
                size="small"
                strokeColor={getImpactColor(recommendation.impact)}
              />
              <div style={{ fontSize: '11px', color: '#999', marginTop: '2px' }}>
                {(recommendation.impact * 100).toFixed(0)}% improvement
              </div>
            </div>

            {/* Priority */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                Priority Score
              </div>
              <Rate
                value={Math.round(recommendation.priority / 20)}
                disabled
                style={{ fontSize: '14px' }}
              />
              <div style={{ fontSize: '11px', color: '#999', marginTop: '2px' }}>
                {recommendation.priority?.toFixed(0)} / 100
              </div>
            </div>

            {/* CTR (if available) */}
            {showMetrics && recommendation.ctr && (
              <div style={{ paddingTop: '8px', borderTop: '1px solid #ddd' }}>
                <Statistic
                  size="small"
                  title="CTR"
                  value={recommendation.ctr}
                  suffix="%"
                  valueStyle={{ fontSize: '12px' }}
                />
              </div>
            )}
          </div>
        </Col>
      </Row>
    </Card>
  );
};

export default RecommendationCard;
