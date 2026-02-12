/**
 * Phase 13: Trace Viewer
 * Distributed trace visualization with waterfall timeline
 */

import React, { useState, useEffect } from 'react';
import {
  Card, Tabs, Table, Tree, Timeline, Button, Modal, Row, Col,
  Statistic, Badge, message, Spin, Empty, Tag, Tooltip, CopyOutlined,
} from 'antd';
import {
  LineChartOutlined, DownloadOutlined, ReloadOutlined,
  CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined,
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as ChartTooltip, ResponsiveContainer } from 'recharts';

const TraceViewer = ({ traceId }) => {
  const [trace, setTrace] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('waterfall');
  const [selectedSpan, setSelectedSpan] = useState(null);
  const [expandedKeys, setExpandedKeys] = useState([]);

  useEffect(() => {
    if (traceId) {
      loadTrace();
    }
  }, [traceId]);

  const loadTrace = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/monitoring/traces/${traceId}`, {
        headers: { 'x-tenant-id': 'current-tenant' },
      });
      if (res.ok) {
        const data = await res.json();
        setTrace(data);
        message.success('Trace loaded');
      }
    } catch (error) {
      message.error('Failed to load trace');
    } finally {
      setLoading(false);
    }
  };

  const handleExportTrace = () => {
    if (!trace) return;

    const dataStr = JSON.stringify(trace, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `trace-${trace.trace_id}.json`;
    link.click();
    message.success('Trace exported');
  };

  const renderWaterfall = () => {
    if (!trace || !trace.spans) {
      return <Empty description="No spans" />;
    }

    const startTime = trace.start_time;
    const spans = trace.spans || [];

    return (
      <div style={{ padding: '20px' }}>
        <div style={{ marginBottom: '20px', overflowX: 'auto' }}>
          {spans.map((span, idx) => {
            const offset = (span.start_time - startTime) * 100;
            const duration = (span.duration_ms / (trace.duration_ms || 1)) * 100;

            return (
              <div key={span.span_id} style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
                  <span
                    style={{
                      minWidth: '200px',
                      fontWeight: 500,
                      cursor: 'pointer',
                      color: '#1890ff',
                      textDecoration: 'underline',
                    }}
                    onClick={() => setSelectedSpan(span)}
                  >
                    {span.operation_name}
                  </span>
                  <Badge
                    status={span.status === 'success' ? 'success' : 'error'}
                    text={`${span.duration_ms.toFixed(2)}ms`}
                  />
                </div>
                <div
                  style={{
                    width: '100%',
                    height: '24px',
                    backgroundColor: '#f0f0f0',
                    borderRadius: '4px',
                    position: 'relative',
                  }}
                >
                  <div
                    style={{
                      position: 'absolute',
                      left: `${offset}%`,
                      width: `${duration}%`,
                      height: '100%',
                      backgroundColor: span.status === 'success' ? '#52c41a' : '#ff4d4f',
                      borderRadius: '4px',
                      opacity: 0.7,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderSpanDetails = () => {
    if (!selectedSpan) {
      return <Empty description="Select a span from waterfall view" />;
    }

    return (
      <Card title={`Span: ${selectedSpan.operation_name}`}>
        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          <Col xs={24} sm={12} lg={6}>
            <Statistic
              title="Duration"
              value={selectedSpan.duration_ms}
              suffix="ms"
              prefix={<ClockCircleOutlined />}
            />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Statistic
              title="Status"
              value={selectedSpan.status}
              prefix={
                selectedSpan.status === 'success' ? (
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                ) : (
                  <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                )
              }
            />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Statistic title="Span ID" value={selectedSpan.span_id.slice(0, 8)} />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Statistic title="Logs" value={selectedSpan.logs?.length || 0} />
          </Col>
        </Row>

        <Tabs
          items={[
            {
              key: 'tags',
              label: 'Tags',
              children: (
                <Table
                  dataSource={Object.entries(selectedSpan.tags || {}).map(([key, value]) => ({
                    key,
                    name: key,
                    value: String(value),
                  }))}
                  columns={[
                    { title: 'Key', dataIndex: 'name', key: 'name', width: 150 },
                    {
                      title: 'Value',
                      dataIndex: 'value',
                      key: 'value',
                      render: (text) => <code>{text}</code>,
                    },
                  ]}
                  pagination={false}
                  size="small"
                />
              ),
            },
            {
              key: 'metrics',
              label: 'Metrics',
              children: (
                <Table
                  dataSource={Object.entries(selectedSpan.metrics || {}).map(([key, value]) => ({
                    key,
                    name: key,
                    value: value.toFixed(2),
                  }))}
                  columns={[
                    { title: 'Metric', dataIndex: 'name', key: 'name', width: 150 },
                    { title: 'Value', dataIndex: 'value', key: 'value' },
                  ]}
                  pagination={false}
                  size="small"
                />
              ),
            },
            {
              key: 'logs',
              label: 'Logs',
              children:
                selectedSpan.logs && selectedSpan.logs.length > 0 ? (
                  <Timeline>
                    {selectedSpan.logs.map((log, idx) => (
                      <Timeline.Item key={idx} color={log.level === 'error' ? 'red' : 'blue'}>
                        <p>
                          <strong>{log.message}</strong>
                          <span style={{ color: '#999', marginLeft: '8px' }}>
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </span>
                        </p>
                      </Timeline.Item>
                    ))}
                  </Timeline>
                ) : (
                  <Empty description="No logs" />
                ),
            },
          ]}
        />
      </Card>
    );
  };

  const renderServiceDependencies = () => {
    if (!trace) {
      return <Empty description="No trace data" />;
    }

    const dependencies = [
      { service: 'API Gateway', upstreamServices: ['Auth Service', 'Workflow Engine'] },
      { service: 'Auth Service', upstreamServices: ['Database'] },
      { service: 'Workflow Engine', upstreamServices: ['Database', 'Cache'] },
      { service: 'Database', upstreamServices: [] },
      { service: 'Cache', upstreamServices: [] },
    ];

    return (
      <div style={{ padding: '20px' }}>
        <Card title="Service Dependency Graph">
          <Tree
            defaultExpandedKeys={['0']}
            treeData={dependencies.map((dep, idx) => ({
              title: `${dep.service}`,
              key: idx,
              children: dep.upstreamServices.map((service, sidx) => ({
                title: service,
                key: `${idx}-${sidx}`,
                isLeaf: true,
              })),
            }))}
          />
        </Card>
      </div>
    );
  };

  const renderCriticalPath = () => {
    if (!trace || !trace.critical_path) {
      return <Empty description="No critical path data" />;
    }

    const pathSpans = trace.critical_path.map((spanId) =>
      trace.spans.find((s) => s.span_id === spanId)
    );

    return (
      <Card title="Critical Path">
        <Timeline>
          {pathSpans.map(
            (span, idx) =>
              span && (
                <Timeline.Item key={span.span_id} color={span.status === 'success' ? 'green' : 'red'}>
                  <p>
                    <strong>
                      {idx + 1}. {span.operation_name}
                    </strong>
                    <span style={{ marginLeft: '12px', color: '#999' }}>
                      {span.duration_ms.toFixed(2)}ms
                    </span>
                  </p>
                </Timeline.Item>
              )
          )}
        </Timeline>

        <div style={{ marginTop: '24px' }}>
          <Statistic
            title="Total Critical Path Duration"
            value={(trace.critical_path.reduce((sum, spanId) => {
              const span = trace.spans.find((s) => s.span_id === spanId);
              return sum + (span ? span.duration_ms : 0);
            }, 0)).toFixed(2)}
            suffix="ms"
          />
        </div>
      </Card>
    );
  };

  return (
    <Card
      title={<span><LineChartOutlined /> Trace Viewer</span>}
      style={{ marginBottom: '24px' }}
      extra={
        <div>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadTrace}
            style={{ marginRight: '8px' }}
          >
            Refresh
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={handleExportTrace}
            disabled={!trace}
          >
            Export
          </Button>
        </div>
      }
    >
      <Spin spinning={loading}>
        {trace && (
          <>
            <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
              <Col xs={24} sm={12} lg={6}>
                <Statistic
                  title="Trace Duration"
                  value={trace.duration_ms}
                  suffix="ms"
                  prefix={<ClockCircleOutlined />}
                />
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Statistic
                  title="Total Spans"
                  value={trace.span_count}
                  prefix={<LineChartOutlined />}
                />
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Statistic
                  title="Status"
                  value={trace.status}
                  prefix={
                    trace.status === 'success' ? (
                      <CheckCircleOutlined style={{ color: '#52c41a' }} />
                    ) : (
                      <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                    )
                  }
                />
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Statistic title="Trace ID" value={trace.trace_id.slice(0, 8)} />
              </Col>
            </Row>

            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              items={[
                {
                  key: 'waterfall',
                  label: 'Waterfall Timeline',
                  children: renderWaterfall(),
                },
                {
                  key: 'details',
                  label: 'Span Details',
                  children: renderSpanDetails(),
                },
                {
                  key: 'dependencies',
                  label: 'Service Dependencies',
                  children: renderServiceDependencies(),
                },
                {
                  key: 'critical-path',
                  label: 'Critical Path',
                  children: renderCriticalPath(),
                },
              ]}
            />
          </>
        )}
      </Spin>
    </Card>
  );
};

export default TraceViewer;
