import React, { useState } from 'react';
import { Card, Tabs, Row, Col, Statistic, Progress, List, Button, Alert, Tag, Divider, Spin } from 'antd';
import { DollarOutlined, ThunderboltOutlined, BugOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import axios from 'axios';

const WorkflowOptimizer = ({ workflowId = 'wf_1' }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadOptimizationAnalysis = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`/api/v1/ai/workflows/${workflowId}/optimize`, {
        executions: [
          {
            id: 'exec_1',
            duration: 25.5,
            status: 'success',
            nodes: [
              { id: 'node_1', action_type: 'send_email', duration: 5, status: 'success' },
              { id: 'node_2', action_type: 'query_data', duration: 15, status: 'success' },
              { id: 'node_3', action_type: 'log_event', duration: 5.5, status: 'success' },
            ],
          },
          {
            id: 'exec_2',
            duration: 28.0,
            status: 'success',
            nodes: [
              { id: 'node_1', action_type: 'send_email', duration: 5.2, status: 'success' },
              { id: 'node_2', action_type: 'query_data', duration: 17.8, status: 'success' },
              { id: 'node_3', action_type: 'log_event', duration: 5, status: 'success' },
            ],
          },
        ],
      });

      setAnalysis(response.data.analysis);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load optimization analysis');
    } finally {
      setLoading(false);
    }
  };

  const renderOverviewTab = () => {
    if (!analysis) return null;

    const perf = analysis.performance || {};
    const cost = analysis.cost || {};

    return (
      <div>
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <Statistic
              title="Health Score"
              value={analysis.health_score}
              suffix="/ 100"
              valueStyle={{ color: analysis.health_score > 80 ? '#52c41a' : '#faad14' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Avg Execution Time"
              value={perf.avg_duration}
              suffix="s"
              prefix={<ThunderboltOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Success Rate"
              value={(perf.success_rate * 100).toFixed(1)}
              suffix="%"
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Avg Cost/Execution"
              value={cost.avg_cost_per_execution}
              prefix={<DollarOutlined />}
              precision={4}
            />
          </Col>
        </Row>

        <Card title="Performance Summary">
          <Row gutter={16}>
            <Col span={12}>
              <div style={{ marginBottom: '16px' }}>
                <div style={{ marginBottom: '8px', fontWeight: 'bold' }}>
                  Execution Time Distribution
                </div>
                <Progress
                  type="circle"
                  percent={Math.round((perf.avg_duration / (perf.max_duration || 100)) * 100)}
                  width={100}
                />
              </div>
            </Col>
            <Col span={12}>
              <div style={{ marginBottom: '16px' }}>
                <div style={{ marginBottom: '8px', fontWeight: 'bold' }}>
                  Success Rate
                </div>
                <Progress
                  type="circle"
                  percent={Math.round(perf.success_rate * 100)}
                  width={100}
                  strokeColor={perf.success_rate > 0.95 ? '#52c41a' : '#faad14'}
                />
              </div>
            </Col>
          </Row>
        </Card>
      </div>
    );
  };

  const renderBottlenecksTab = () => {
    if (!analysis || !analysis.performance) return null;

    const bottlenecks = analysis.performance.bottlenecks || [];

    if (bottlenecks.length === 0) {
      return (
        <Alert
          message="No Bottlenecks Found"
          description="Your workflow is performing optimally with no identified bottlenecks."
          type="success"
          icon={<ThunderboltOutlined />}
        />
      );
    }

    return (
      <List
        dataSource={bottlenecks}
        renderItem={(bottleneck, idx) => (
          <List.Item key={idx}>
            <List.Item.Meta
              avatar={
                <ExclamationCircleOutlined style={{
                  color: bottleneck.severity === 'high' ? '#f5222d' : '#faad14',
                  fontSize: '20px'
                }} />
              }
              title={
                <div>
                  {bottleneck.type.replace(/_/g, ' ').toUpperCase()}
                  <Tag color={bottleneck.severity === 'high' ? 'red' : 'orange'} style={{ marginLeft: '8px' }}>
                    {bottleneck.severity}
                  </Tag>
                </div>
              }
              description={
                <div>
                  <div>Node: {bottleneck.node_id}</div>
                  <div style={{ fontSize: '12px', color: '#999' }}>
                    {bottleneck.description || bottleneck.impact}
                  </div>
                </div>
              }
            />
            <Button type="primary" size="small">Fix</Button>
          </List.Item>
        )}
      />
    );
  };

  const renderCostTab = () => {
    if (!analysis || !analysis.cost) return null;

    const cost = analysis.cost;
    const costDrivers = cost.cost_drivers || [];

    const chartData = costDrivers.map(driver => ({
      name: driver.action.replace(/_/g, ' '),
      value: parseFloat(driver.total_cost),
    }));

    const COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#13c2c2'];

    return (
      <Tabs>
        <Tabs.TabPane label="Cost Breakdown" key="breakdown">
          <Row gutter={16} style={{ marginBottom: '24px' }}>
            <Col span={12}>
              <Statistic
                title="Total Cost"
                value={cost.total_cost}
                prefix={<DollarOutlined />}
                precision={4}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="Monthly Forecast"
                value={cost.monthly_forecast?.total_estimated_monthly}
                prefix={<DollarOutlined />}
                precision={2}
              />
            </Col>
          </Row>

          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: $${value.toFixed(2)}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `$${value.toFixed(4)}`} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane label="Cost Optimization" key="optimization">
          <List
            dataSource={cost.optimization_opportunities || []}
            renderItem={(opp, idx) => (
              <List.Item key={idx}>
                <List.Item.Meta
                  title={opp.type.replace(/_/g, ' ').toUpperCase()}
                  description={
                    <div>
                      <div>{opp.suggestion}</div>
                      <div style={{ fontSize: '12px', color: '#52c41a', marginTop: '4px' }}>
                        Potential Savings: ${opp.potential_savings.toFixed(4)}
                      </div>
                    </div>
                  }
                />
                <Button type="primary" size="small">Apply</Button>
              </List.Item>
            )}
          />
        </Tabs.TabPane>
      </Tabs>
    );
  };

  const renderAnomaliesTab = () => {
    if (!analysis || !analysis.anomalies) return null;

    const anomalies = analysis.anomalies;

    if (anomalies.length === 0) {
      return (
        <Alert
          message="No Anomalies Detected"
          description="Your workflow is executing as expected with no detected anomalies."
          type="success"
        />
      );
    }

    return (
      <List
        dataSource={anomalies}
        renderItem={(anomaly, idx) => (
          <List.Item key={idx}>
            <List.Item.Meta
              avatar={<BugOutlined style={{ fontSize: '20px', color: '#f5222d' }} />}
              title={
                <div>
                  {anomaly.type.replace(/_/g, ' ').toUpperCase()}
                  <Tag color="red" style={{ marginLeft: '8px' }}>
                    {anomaly.severity}
                  </Tag>
                </div>
              }
              description={
                <div>
                  <div>{anomaly.description}</div>
                  <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
                    {anomaly.deviation && `Deviation: ${anomaly.deviation}σ`}
                  </div>
                </div>
              }
            />
            <Button type="primary" danger size="small">Investigate</Button>
          </List.Item>
        )}
      />
    );
  };

  const renderRecommendationsTab = () => {
    if (!analysis || !analysis.optimization_plan) return null;

    const plan = analysis.optimization_plan;

    return (
      <Tabs>
        <Tabs.TabPane label="Quick Wins" key="quick">
          {plan.quick_wins?.length > 0 ? (
            <List
              dataSource={plan.quick_wins}
              renderItem={(win, idx) => (
                <List.Item key={idx}>
                  <List.Item.Meta
                    title={`${win.type.toUpperCase()} - Easy to Implement`}
                    description={
                      <div>
                        <div>{win.description}</div>
                        <div style={{ fontSize: '12px', color: '#52c41a', marginTop: '4px' }}>
                          Estimated Savings: ${win.savings?.toFixed(2) || 'N/A'}
                        </div>
                      </div>
                    }
                  />
                  <Button type="primary" size="small">Apply Now</Button>
                </List.Item>
              )}
            />
          ) : (
            <Alert message="No quick wins identified" type="info" />
          )}
        </Tabs.TabPane>

        <Tabs.TabPane label="Priority Improvements" key="priority">
          {plan.priority_improvements?.length > 0 ? (
            <List
              dataSource={plan.priority_improvements}
              renderItem={(imp, idx) => (
                <List.Item key={idx}>
                  <List.Item.Meta
                    title={imp.type.replace(/_/g, ' ').toUpperCase()}
                    description={
                      <div>
                        <div>{imp.description}</div>
                        <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
                          Potential Causes: {imp.potential_causes?.map(c => c.cause).join(', ') || 'N/A'}
                        </div>
                      </div>
                    }
                  />
                  <Tag color="red">Urgent</Tag>
                </List.Item>
              )}
            />
          ) : (
            <Alert message="No priority improvements needed" type="success" />
          )}
        </Tabs.TabPane>

        <Tabs.TabPane label="Medium Term" key="medium">
          {plan.medium_term?.length > 0 ? (
            <List
              dataSource={plan.medium_term}
              renderItem={(opt, idx) => (
                <List.Item key={idx}>
                  <List.Item.Meta
                    title={opt.type.replace(/_/g, ' ').toUpperCase()}
                    description={
                      <div>
                        <div>Nodes: {opt.nodes?.join(', ') || 'N/A'}</div>
                        <div style={{ fontSize: '12px', color: '#1890ff', marginTop: '4px' }}>
                          Potential Speedup: {opt.speedup?.toFixed(1)}x
                        </div>
                      </div>
                    }
                  />
                  <Tag color="blue">Medium Effort</Tag>
                </List.Item>
              )}
            />
          ) : (
            <Alert message="No medium-term improvements identified" type="info" />
          )}
        </Tabs.TabPane>
      </Tabs>
    );
  };

  return (
    <div style={{ padding: '24px', background: '#fafafa', minHeight: '100vh' }}>
      <Card
        title="🚀 Workflow Optimizer"
        style={{ maxWidth: '1200px', margin: '0 auto' }}
        extra={
          <Button type="primary" onClick={loadOptimizationAnalysis} loading={loading}>
            {analysis ? 'Refresh Analysis' : 'Run Analysis'}
          </Button>
        }
      >
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
          <div style={{ textAlign: 'center', padding: '60px' }}>
            <Spin size="large" />
          </div>
        ) : analysis ? (
          <Tabs activeKey={activeTab} onChange={setActiveTab}>
            <Tabs.TabPane label="Overview" key="overview">
              {renderOverviewTab()}
            </Tabs.TabPane>
            <Tabs.TabPane label="Bottlenecks" key="bottlenecks">
              {renderBottlenecksTab()}
            </Tabs.TabPane>
            <Tabs.TabPane label="Cost Analysis" key="cost">
              {renderCostTab()}
            </Tabs.TabPane>
            <Tabs.TabPane label="Anomalies" key="anomalies">
              {renderAnomaliesTab()}
            </Tabs.TabPane>
            <Tabs.TabPane label="Recommendations" key="recommendations">
              {renderRecommendationsTab()}
            </Tabs.TabPane>
          </Tabs>
        ) : (
          <Alert
            message="No Analysis Available"
            description="Click 'Run Analysis' to analyze your workflow for optimization opportunities."
            type="info"
          />
        )}
      </Card>
    </div>
  );
};

export default WorkflowOptimizer;
