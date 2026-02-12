"""
RealTimeDashboard Component

WebSocket-powered real-time dashboard with:
- Live metric updates
- Segment distribution
- Churn alerts
- Recommendation performance
- System health monitoring
"""

import React, { useState, useEffect, useRef } from 'react';
import { Card, Row, Col, Statistic, Alert, Badge, Table, Spin, Tag, Tabs } from 'antd';
import { 
  ArrowUpOutlined, ArrowDownOutlined, 
  AlertOutlined, HeartOutlined, DatabaseOutlined 
} from '@ant-design/icons';

const RealTimeDashboard = () => {
  const [metrics, setMetrics] = useState({
    overview: null,
    segments: null,
    alerts: [],
    recommendations: null,
    health: null
  });
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const wsRef = useRef(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const token = localStorage.getItem('token');
    const clientId = `client_${Date.now()}`;
    const wsUrl = `ws://localhost:8001/api/v1/phase9/ws/dashboard/${clientId}`;

    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      setConnected(true);
      setLoading(false);
      console.log('WebSocket connected');
      
      // Subscribe to updates
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        dashboard_type: 'overview'
      }));

      // Send heartbeat
      setInterval(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: 'heartbeat' }));
        }
      }, 30000);
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'overview_metrics') {
        setMetrics(prev => ({ ...prev, overview: data.data }));
      } else if (data.type === 'segment_metrics') {
        setMetrics(prev => ({ ...prev, segments: data.data }));
      } else if (data.type === 'churn_alerts') {
        setMetrics(prev => ({ ...prev, alerts: data.data.alerts }));
      } else if (data.type === 'recommendation_performance') {
        setMetrics(prev => ({ ...prev, recommendations: data.data }));
      } else if (data.type === 'system_health') {
        setMetrics(prev => ({ ...prev, health: data.data }));
      }
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    wsRef.current.onclose = () => {
      setConnected(false);
      console.log('WebSocket disconnected');
      // Reconnect after 5 seconds
      setTimeout(connectWebSocket, 5000);
    };
  };

  const segmentColumns = [
    { title: 'Segment', dataIndex: 'name', key: 'name' },
    {
      title: 'Count',
      dataIndex: 'count',
      key: 'count',
      render: (value) => <strong>{value}</strong>
    },
    {
      title: 'Avg LTV',
      dataIndex: 'avg_ltv',
      key: 'ltv',
      render: (value) => `$${value?.toFixed(2) || 0}`
    },
    {
      title: 'Churn Risk',
      dataIndex: 'churn_risk',
      key: 'churn',
      render: (value) => {
        const risk = value?.toFixed(2) || 0;
        const color = risk > 0.6 ? 'red' : risk > 0.3 ? 'orange' : 'green';
        return <Tag color={color}>{(risk * 100).toFixed(0)}%</Tag>;
      }
    }
  ];

  const alertColumns = [
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      render: (value) => (
        <Badge count={value} style={{ backgroundColor: '#ff4d4f' }} />
      )
    },
    {
      title: 'Customer ID',
      dataIndex: 'customer_id',
      key: 'customer'
    },
    {
      title: 'Risk',
      dataIndex: 'churn_probability',
      key: 'risk',
      render: (value) => `${(value * 100).toFixed(0)}%`
    },
    {
      title: 'Action',
      dataIndex: 'recommended_action',
      key: 'action',
      render: (action) => <Tag color="blue">{action}</Tag>
    }
  ];

  if (loading && !connected) {
    return <Spin size="large" tip="Connecting to dashboard..." />;
  }

  const overviewData = metrics.overview || {};

  return (
    <div style={{ padding: '20px' }}>
      <Card
        title="Real-Time Dashboard"
        extra={
          <Badge
            status={connected ? 'success' : 'error'}
            text={connected ? 'LIVE' : 'OFFLINE'}
          />
        }
      >
        <Tabs items={[
          {
            key: '1',
            label: '📊 Overview',
            children: (
              <div>
                <Row gutter={[16, 16]}>
                  <Col xs={24} sm={12} lg={6}>
                    <Statistic
                      title="Total Customers"
                      value={overviewData.total_customers || 0}
                      suffix="👥"
                    />
                  </Col>
                  <Col xs={24} sm={12} lg={6}>
                    <Statistic
                      title="Active (30d)"
                      value={overviewData.active_customers || 0}
                      suffix={<ArrowUpOutlined style={{ color: '#52c41a' }} />}
                    />
                  </Col>
                  <Col xs={24} sm={12} lg={6}>
                    <Statistic
                      title="Activity Rate"
                      value={overviewData.activity_rate?.toFixed(1) || 0}
                      suffix="%"
                    />
                  </Col>
                  <Col xs={24} sm={12} lg={6}>
                    <Statistic
                      title="Churn Rate"
                      value={overviewData.churn_rate?.toFixed(1) || 0}
                      suffix="%"
                      valueStyle={{ color: '#ff4d4f' }}
                    />
                  </Col>
                </Row>

                <Row gutter={[16, 16]} style={{ marginTop: '20px' }}>
                  <Col xs={24} sm={12} lg={6}>
                    <Statistic
                      title="Total Revenue"
                      value={overviewData.total_revenue?.toFixed(0) || 0}
                      prefix="$"
                    />
                  </Col>
                  <Col xs={24} sm={12} lg={6}>
                    <Statistic
                      title="MRR"
                      value={overviewData.mrr?.toFixed(0) || 0}
                      prefix="$"
                      suffix="/mo"
                    />
                  </Col>
                  <Col xs={24} sm={12} lg={6}>
                    <Statistic
                      title="New Signups (7d)"
                      value={overviewData.recent_signups || 0}
                    />
                  </Col>
                </Row>
              </div>
            )
          },
          {
            key: '2',
            label: '🎯 Segments',
            children: metrics.segments ? (
              <Row gutter={[16, 16]}>
                {Object.entries(metrics.segments).map(([name, data]) => (
                  <Col xs={24} sm={12} lg={6} key={name}>
                    <Card size="small">
                      <Statistic
                        title={name}
                        value={data.count}
                        suffix="👤"
                      />
                      <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
                        Avg LTV: ${data.avg_ltv?.toFixed(0) || 0}
                      </div>
                      <Tag color={data.churn_risk > 0.6 ? 'red' : 'green'} style={{ marginTop: '8px' }}>
                        Churn: {(data.churn_risk * 100).toFixed(0)}%
                      </Tag>
                    </Card>
                  </Col>
                ))}
              </Row>
            ) : (
              <Spin />
            )
          },
          {
            key: '3',
            label: '🚨 Alerts',
            children: metrics.alerts?.length > 0 ? (
              <Table
                columns={alertColumns}
                dataSource={metrics.alerts}
                rowKey="alert_id"
                size="small"
                pagination={{ pageSize: 5 }}
              />
            ) : (
              <Alert message="No active alerts" type="success" showIcon />
            )
          },
          {
            key: '4',
            label: '💡 Recommendations',
            children: metrics.recommendations ? (
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} lg={6}>
                  <Statistic
                    title="Total Sent"
                    value={metrics.recommendations.total_recommendations_sent || 0}
                  />
                </Col>
                <Col xs={24} sm={12} lg={6}>
                  <Statistic
                    title="Click-Through Rate"
                    value={metrics.recommendations.click_through_rate?.toFixed(2) || 0}
                    suffix="%"
                  />
                </Col>
                <Col xs={24} sm={12} lg={6}>
                  <Statistic
                    title="Conversion Rate"
                    value={metrics.recommendations.conversion_rate?.toFixed(2) || 0}
                    suffix="%"
                  />
                </Col>
              </Row>
            ) : (
              <Spin />
            )
          },
          {
            key: '5',
            label: '🏥 System Health',
            children: metrics.health ? (
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12}>
                  <Card size="small">
                    <h4>Database</h4>
                    <Tag color={metrics.health.data.database.status === 'healthy' ? 'green' : 'red'}>
                      {metrics.health.data.database.status?.toUpperCase()}
                    </Tag>
                    <div style={{ fontSize: '12px', marginTop: '8px' }}>
                      Response: {metrics.health.data.database.response_time_ms}ms
                    </div>
                  </Card>
                </Col>
                <Col xs={24} sm={12}>
                  <Card size="small">
                    <h4>API</h4>
                    <Tag color={metrics.health.data.api.status === 'healthy' ? 'green' : 'red'}>
                      {metrics.health.data.api.status?.toUpperCase()}
                    </Tag>
                    <div style={{ fontSize: '12px', marginTop: '8px' }}>
                      Requests/min: {metrics.health.data.api.requests_per_minute}
                    </div>
                  </Card>
                </Col>
              </Row>
            ) : (
              <Spin />
            )
          }
        ]} />
      </Card>
    </div>
  );
};

export default RealTimeDashboard;
