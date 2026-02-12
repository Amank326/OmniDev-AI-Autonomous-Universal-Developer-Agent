/**
 * Phase 13: Observability Dashboard
 * Comprehensive monitoring and observability interface
 */

import React, { useState, useEffect } from 'react';
import {
  Tabs, Card, Row, Col, Statistic, Select, DatePicker, Button,
  Spin, Empty, message, Tooltip, Badge, Avatar, Timeline,
  LineChart, BarChart, AreaChart, Line, Bar, Area, XAxis, YAxis, CartesianGrid, Legend, ResponsiveContainer,
} from 'antd';
import {
  DashboardOutlined, BarChartOutlined, LineChartOutlined,
  BugOutlined, AlertOutlined, DollarOutlined, CheckCircleOutlined,
  ClockCircleOutlined, WarningOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';

const ObservabilityDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState([dayjs().subtract(7, 'days'), dayjs()]);

  // Data states
  const [traces, setTraces] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [sloStatus, setSloStatus] = useState({});
  const [anomalies, setAnomalies] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [costs, setCosts] = useState({});

  const [tracingStats, setTracingStats] = useState({});
  const [metricsData, setMetricsData] = useState([]);
  const [alertStats, setAlertStats] = useState({});
  const [costData, setCostData] = useState([]);

  // Filters
  const [selectedMetric, setSelectedMetric] = useState('http_request_duration_ms');
  const [traceFilter, setTraceFilter] = useState('all');

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Load traces
      const tracesRes = await fetch('/api/v1/monitoring/traces?limit=20', {
        headers: { 'x-tenant-id': 'current-tenant' },
      });
      if (tracesRes.ok) {
        const data = await tracesRes.json();
        setTraces(data.traces || []);
        setTracingStats({
          total_traces: data.traces?.length || 0,
          avg_duration: calculateAvg(data.traces?.map(t => t.duration_ms) || []),
          error_rate: ((data.traces?.filter(t => t.status === 'failed').length || 0) / (data.traces?.length || 1)) * 100,
        });
      }

      // Load metrics
      const metricsRes = await fetch('/api/v1/monitoring/metrics', {
        headers: { 'x-tenant-id': 'current-tenant' },
      });
      if (metricsRes.ok) {
        const data = await metricsRes.json();
        setMetrics(data.metrics || []);
      }

      // Load alerts
      const alertsRes = await fetch('/api/v1/monitoring/alerts', {
        headers: { 'x-tenant-id': 'current-tenant' },
      });
      if (alertsRes.ok) {
        const data = await alertsRes.json();
        setAlerts(data.alerts || []);
        setAlertStats({
          open: data.alerts?.filter(a => a.status === 'open').length || 0,
          acknowledged: data.alerts?.filter(a => a.status === 'acknowledged').length || 0,
          resolved: data.alerts?.filter(a => a.status === 'resolved').length || 0,
        });
      }

      // Load costs
      const costsRes = await fetch('/api/v1/monitoring/costs/breakdown?group_by=category', {
        headers: { 'x-tenant-id': 'current-tenant' },
      });
      if (costsRes.ok) {
        const data = await costsRes.json();
        setCosts(data.breakdown || {});
      }

      // Load anomalies
      const anomaliesRes = await fetch('/api/v1/monitoring/anomalies?hours=24&limit=10', {
        headers: { 'x-tenant-id': 'current-tenant' },
      });
      if (anomaliesRes.ok) {
        const data = await anomaliesRes.json();
        setAnomalies(data.anomalies || []);
      }

      message.success('Dashboard updated');
    } catch (error) {
      console.error('Error loading dashboard:', error);
      message.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const calculateAvg = (values) => {
    if (!values || values.length === 0) return 0;
    return (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2);
  };

  const handleAcknowledgeAlert = async (alertId) => {
    try {
      const res = await fetch(`/api/v1/monitoring/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: {
          'x-tenant-id': 'current-tenant',
          'x-user-id': 'current-user',
        },
      });
      if (res.ok) {
        message.success('Alert acknowledged');
        loadDashboardData();
      }
    } catch (error) {
      message.error('Failed to acknowledge alert');
    }
  };

  const renderOverview = () => (
    <div style={{ padding: '20px' }}>
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Traces"
              value={tracingStats.total_traces || 0}
              prefix={<LineChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Avg Latency"
              value={tracingStats.avg_duration || 0}
              suffix="ms"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Error Rate"
              value={tracingStats.error_rate || 0}
              suffix="%"
              prefix={<WarningOutlined />}
              valueStyle={{ color: tracingStats.error_rate > 1 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Alerts"
              value={alertStats.open || 0}
              prefix={<AlertOutlined />}
              valueStyle={{ color: alertStats.open > 0 ? '#ff7a45' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="Recent Traces" style={{ marginBottom: '24px' }}>
        {traces.length > 0 ? (
          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {traces.slice(0, 5).map((trace) => (
              <div key={trace.trace_id} style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                <div>
                  <Badge
                    status={trace.status === 'success' ? 'success' : 'error'}
                    text={`${trace.request_method} ${trace.request_path}`}
                  />
                  <span style={{ float: 'right', color: '#999' }}>
                    {trace.duration_ms.toFixed(2)}ms · {trace.span_count} spans
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <Empty description="No traces" />
        )}
      </Card>

      <Card title="Active Alerts" style={{ marginBottom: '24px' }}>
        {alerts.length > 0 ? (
          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {alerts.slice(0, 5).map((alert) => (
              <div
                key={alert.alert_id}
                style={{
                  padding: '12px',
                  marginBottom: '8px',
                  backgroundColor: alert.severity === 'critical' ? '#fff2f0' : '#fef3c7',
                  borderRadius: '4px',
                  borderLeft: `4px solid ${alert.severity === 'critical' ? '#ff4d4f' : '#fbbf24'}`,
                }}
              >
                <div style={{ fontWeight: 'bold' }}>{alert.title}</div>
                <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                  {alert.description}
                </div>
                {alert.status === 'open' && (
                  <Button
                    size="small"
                    type="primary"
                    style={{ marginTop: '8px' }}
                    onClick={() => handleAcknowledgeAlert(alert.alert_id)}
                  >
                    Acknowledge
                  </Button>
                )}
              </div>
            ))}
          </div>
        ) : (
          <Empty description="No active alerts" />
        )}
      </Card>
    </div>
  );

  const renderMetrics = () => (
    <div style={{ padding: '20px' }}>
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={16}>
          <Col xs={24} sm={12}>
            <Select
              value={selectedMetric}
              onChange={setSelectedMetric}
              style={{ width: '100%' }}
              placeholder="Select metric"
              options={metrics.map(m => ({ label: m.name, value: m.name }))}
            />
          </Col>
          <Col xs={24} sm={12}>
            <Button type="primary" block onClick={loadDashboardData}>
              Refresh
            </Button>
          </Col>
        </Row>
      </Card>

      <Card title={`Metric: ${selectedMetric}`}>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={metricsData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="value" stroke="#1890ff" isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );

  const renderSLAandSLO = () => (
    <div style={{ padding: '20px' }}>
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Availability SLO"
              value={99.5}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Error Budget"
              value={0.5}
              suffix="%"
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="P99 Latency"
              value={250}
              suffix="ms"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="SLA Status"
              value="Healthy"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="SLO Compliance">
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={[
            { time: '00:00', compliance: 99.8 },
            { time: '04:00', compliance: 99.7 },
            { time: '08:00', compliance: 99.5 },
            { time: '12:00', compliance: 99.6 },
            { time: '16:00', compliance: 99.9 },
            { time: '20:00', compliance: 99.8 },
          ]}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis domain={[99, 100]} />
            <Tooltip />
            <Area type="monotone" dataKey="compliance" fill="#8884d8" stroke="#1890ff" />
          </AreaChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );

  const renderAnomalies = () => (
    <div style={{ padding: '20px' }}>
      <Card title={`Recent Anomalies (${anomalies.length})`}>
        {anomalies.length > 0 ? (
          <Timeline>
            {anomalies.map((anomaly) => (
              <Timeline.Item
                key={anomaly.anomaly_id}
                color={anomaly.severity > 0.7 ? 'red' : anomaly.severity > 0.4 ? 'orange' : 'blue'}
                dot={<BugOutlined />}
              >
                <p>
                  <strong>{anomaly.metric_name}</strong> - {anomaly.anomaly_type}
                  <span style={{ color: '#999', marginLeft: '8px' }}>
                    Severity: {(anomaly.severity * 100).toFixed(1)}%
                  </span>
                </p>
                <p style={{ fontSize: '12px', color: '#666' }}>
                  Value: {anomaly.value.toFixed(2)} vs Baseline: {anomaly.baseline.toFixed(2)}
                </p>
              </Timeline.Item>
            ))}
          </Timeline>
        ) : (
          <Empty description="No anomalies detected" />
        )}
      </Card>
    </div>
  );

  const renderCosts = () => (
    <div style={{ padding: '20px' }}>
      <Card title="Cost Breakdown" style={{ marginBottom: '24px' }}>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={Object.entries(costs).map(([category, amount]) => ({
              category,
              amount,
            }))}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="category" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="amount" fill="#8884d8" />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card title="Monthly Trend">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={[
            { month: 'Jan', cost: 1200 },
            { month: 'Feb', cost: 1400 },
            { month: 'Mar', cost: 1300 },
            { month: 'Apr', cost: 1500 },
          ]}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip formatter={(value) => `$${value}`} />
            <Line type="monotone" dataKey="cost" stroke="#82ca9d" />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      <Card title={<span><DashboardOutlined /> Observability Dashboard</span>} style={{ marginBottom: '24px' }}>
        <Spin spinning={loading}>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={[
              {
                key: 'overview',
                label: 'Overview',
                icon: <DashboardOutlined />,
                children: renderOverview(),
              },
              {
                key: 'metrics',
                label: 'Metrics',
                icon: <BarChartOutlined />,
                children: renderMetrics(),
              },
              {
                key: 'sla',
                label: 'SLA/SLO',
                icon: <CheckCircleOutlined />,
                children: renderSLAandSLO(),
              },
              {
                key: 'anomalies',
                label: 'Anomalies',
                icon: <BugOutlined />,
                children: renderAnomalies(),
              },
              {
                key: 'alerts',
                label: 'Alerts',
                icon: <AlertOutlined />,
                children: <Card>{renderAlerts()}</Card>,
              },
              {
                key: 'costs',
                label: 'Costs',
                icon: <DollarOutlined />,
                children: renderCosts(),
              },
            ]}
          />
        </Spin>
      </Card>
    </div>
  );

  function renderAlerts() {
    return (
      <div style={{ padding: '20px' }}>
        {alerts.length > 0 ? (
          alerts.map((alert) => (
            <Card key={alert.alert_id} style={{ marginBottom: '12px' }}>
              <Row>
                <Col span={20}>
                  <div>
                    <Badge
                      status={
                        alert.severity === 'critical'
                          ? 'error'
                          : alert.severity === 'high'
                          ? 'warning'
                          : 'processing'
                      }
                      text={<strong>{alert.title}</strong>}
                    />
                  </div>
                  <p style={{ marginTop: '8px', color: '#666' }}>{alert.description}</p>
                </Col>
                <Col span={4} style={{ textAlign: 'right' }}>
                  {alert.status === 'open' && (
                    <Button
                      type="primary"
                      onClick={() => handleAcknowledgeAlert(alert.alert_id)}
                    >
                      Acknowledge
                    </Button>
                  )}
                </Col>
              </Row>
            </Card>
          ))
        ) : (
          <Empty description="No alerts" />
        )}
      </div>
    );
  }
};

export default ObservabilityDashboard;
