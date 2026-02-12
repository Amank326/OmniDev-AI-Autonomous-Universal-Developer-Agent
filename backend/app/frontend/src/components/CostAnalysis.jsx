/**
 * Phase 13: Cost Analysis
 * Cost optimization and forecasting interface
 */

import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Statistic, Tabs, Button, Modal, Form, Input, Select,
  message, Spin, Empty, Tooltip, Table, Badge,
} from 'antd';
import {
  DollarOutlined, ArrowUpOutlined, ArrowDownOutlined,
  LineChartOutlined, BarChartOutlined, BugOutlined,
} from '@ant-design/icons';
import {
  PieChart, Pie, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip as ChartTooltip,
  Legend, Cell, ResponsiveContainer,
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const CostAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [costBreakdown, setCostBreakdown] = useState({});
  const [monthlyCosts, setMonthlyCosts] = useState([]);
  const [forecast, setForecast] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [showOptimizationModal, setShowOptimizationModal] = useState(false);
  const [budgetForm] = Form.useForm();

  useEffect(() => {
    loadCostData();
  }, []);

  const loadCostData = async () => {
    setLoading(true);
    try {
      // Load cost breakdown
      const breakdownRes = await fetch('/api/v1/monitoring/costs/breakdown?group_by=category', {
        headers: { 'x-tenant-id': 'current-tenant' },
      });
      if (breakdownRes.ok) {
        const data = await breakdownRes.json();
        setCostBreakdown(data.breakdown || {});
      }

      // Load monthly costs
      const monthlyRes = await fetch('/api/v1/monitoring/costs/monthly?months=12', {
        headers: { 'x-tenant-id': 'current-tenant' },
      });
      if (monthlyRes.ok) {
        const data = await monthlyRes.json();
        setMonthlyCosts(data.monthly_costs || []);
      }

      // Load forecast
      const forecastRes = await fetch('/api/v1/monitoring/costs/forecast?months=3', {
        headers: { 'x-tenant-id': 'current-tenant' },
      });
      if (forecastRes.ok) {
        const data = await forecastRes.json();
        setForecast(data.forecast || []);
      }

      // Load recommendations
      const recsRes = await fetch('/api/v1/monitoring/costs/optimizations', {
        headers: { 'x-tenant-id': 'current-tenant' },
      });
      if (recsRes.ok) {
        const data = await recsRes.json();
        setRecommendations(data.recommendations || []);
      }

      message.success('Cost data loaded');
    } catch (error) {
      console.error('Error loading cost data:', error);
      message.error('Failed to load cost data');
    } finally {
      setLoading(false);
    }
  };

  const getTotalCost = () => {
    return Object.values(costBreakdown).reduce((sum, val) => sum + (val || 0), 0);
  };

  const getAverageMonthlyCost = () => {
    if (monthlyCosts.length === 0) return 0;
    const total = monthlyCosts.reduce((sum, m) => sum + (m.total_cost || 0), 0);
    return (total / monthlyCosts.length).toFixed(2);
  };

  const getLatestMonthlyCost = () => {
    return monthlyCosts.length > 0 ? monthlyCosts[monthlyCosts.length - 1].total_cost : 0;
  };

  const getTrendDirection = () => {
    if (monthlyCosts.length < 2) return null;
    const latest = monthlyCosts[monthlyCosts.length - 1].total_cost;
    const previous = monthlyCosts[monthlyCosts.length - 2].total_cost;
    return latest > previous ? 'up' : 'down';
  };

  const getTrendPercent = () => {
    if (monthlyCosts.length < 2) return 0;
    const latest = monthlyCosts[monthlyCosts.length - 1].total_cost;
    const previous = monthlyCosts[monthlyCosts.length - 2].total_cost;
    return ((latest - previous) / previous * 100).toFixed(1);
  };

  const handleOptimizeBudget = async (values) => {
    try {
      const res = await fetch('/api/v1/monitoring/costs/optimize-for-budget', {
        method: 'POST',
        headers: {
          'x-tenant-id': 'current-tenant',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ budget: values.budget }),
      });

      if (res.ok) {
        const data = await res.json();
        Modal.info({
          title: 'Optimization Plan',
          content: (
            <div>
              <p>Current Cost: ${data.current_cost?.toFixed(2)}</p>
              <p>Target Budget: ${values.budget?.toFixed(2)}</p>
              <p>
                Projected Cost After: ${data.projected_cost_after?.toFixed(2)}
              </p>
              <h4>Recommendations:</h4>
              {data.recommendations?.length > 0 ? (
                <ul>
                  {data.recommendations.map((rec, idx) => (
                    <li key={idx}>
                      {rec.title} - Save: ${rec.estimated_savings?.toFixed(2)}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>Already within budget!</p>
              )}
            </div>
          ),
        });
        setShowOptimizationModal(false);
        budgetForm.resetFields();
      }
    } catch (error) {
      message.error('Failed to optimize budget');
    }
  };

  const renderCostBreakdown = () => {
    const data = Object.entries(costBreakdown).map(([category, amount]) => ({
      name: category.replace('_', ' ').toUpperCase(),
      value: amount,
    }));

    if (data.length === 0) {
      return <Empty description="No cost data" />;
    }

    return (
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={true}
            label={({ name, value }) => `${name}: $${value.toFixed(2)}`}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <ChartTooltip formatter={(value) => `$${value.toFixed(2)}`} />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  const renderMonthlyTrend = () => {
    if (monthlyCosts.length === 0) {
      return <Empty description="No monthly data" />;
    }

    return (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={monthlyCosts}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
          <YAxis />
          <ChartTooltip formatter={(value) => `$${value.toFixed(2)}`} />
          <Legend />
          <Line
            type="monotone"
            dataKey="total_cost"
            stroke="#8884d8"
            name="Monthly Cost"
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  const renderForecast = () => {
    if (forecast.length === 0) {
      return <Empty description="No forecast data" />;
    }

    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={forecast}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month_offset" label={{ value: 'Months Ahead', position: 'insideBottom', offset: -5 }} />
          <YAxis />
          <ChartTooltip formatter={(value) => `$${value.toFixed(2)}`} />
          <Legend />
          <Bar dataKey="forecasted_cost" fill="#82ca9d" name="Forecasted Cost" />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  const renderRecommendations = () => {
    if (recommendations.length === 0) {
      return <Empty description="No recommendations available" />;
    }

    const columns = [
      {
        title: 'Recommendation',
        dataIndex: 'title',
        key: 'title',
        width: 200,
      },
      {
        title: 'Description',
        dataIndex: 'description',
        key: 'description',
      },
      {
        title: 'Estimated Savings',
        dataIndex: 'estimated_savings',
        key: 'estimated_savings',
        render: (value) => <strong>${value?.toFixed(2)}</strong>,
      },
      {
        title: 'Priority',
        dataIndex: 'priority',
        key: 'priority',
        render: (priority) => {
          const colors = {
            high: 'red',
            medium: 'orange',
            low: 'blue',
          };
          return <Badge color={colors[priority]} text={priority?.toUpperCase()} />;
        },
      },
      {
        title: 'Action',
        key: 'action',
        render: () => <Button type="link">Implement</Button>,
      },
    ];

    return (
      <Table
        dataSource={recommendations}
        columns={columns}
        pagination={false}
        size="small"
      />
    );
  };

  return (
    <div style={{ padding: '24px', background: '#f0f2f5' }}>
      <Spin spinning={loading}>
        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Total Cost (This Month)"
                value={getLatestMonthlyCost()}
                prefix="$"
                suffix={
                  getTrendDirection() === 'up' ? (
                    <ArrowUpOutlined style={{ color: '#ff4d4f' }} />
                  ) : (
                    <ArrowDownOutlined style={{ color: '#52c41a' }} />
                  )
                }
              />
              <div style={{ fontSize: '12px', color: '#999', marginTop: '8px' }}>
                {getTrendDirection() === 'up' ? 'Up' : 'Down'} {getTrendPercent()}% vs last month
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Average Monthly Cost"
                value={getAverageMonthlyCost()}
                prefix="$"
                prefix={<DollarOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="3-Month Forecast"
                value={
                  forecast.length > 0 &&
                  (forecast.reduce((sum, f) => sum + f.forecasted_cost, 0) / forecast.length).toFixed(2)
                }
                prefix="$"
                valueStyle={{
                  color: forecast.some((f) => f.forecasted_cost > getLatestMonthlyCost())
                    ? '#ff4d4f'
                    : '#52c41a',
                }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Potential Savings"
                value={recommendations.reduce((sum, r) => sum + (r.estimated_savings || 0), 0)}
                prefix="$"
                suffix={`(${recommendations.length} opportunities)`}
              />
            </Card>
          </Col>
        </Row>

        <Tabs
          items={[
            {
              key: 'breakdown',
              label: 'Cost Breakdown',
              icon: <BarChartOutlined />,
              children: (
                <Card title="Costs by Category">
                  {renderCostBreakdown()}
                </Card>
              ),
            },
            {
              key: 'trend',
              label: 'Monthly Trend',
              icon: <LineChartOutlined />,
              children: (
                <Card title="12-Month Cost Trend">
                  {renderMonthlyTrend()}
                </Card>
              ),
            },
            {
              key: 'forecast',
              label: 'Forecast',
              icon: <LineChartOutlined />,
              children: (
                <Card title="3-Month Cost Forecast">
                  {renderForecast()}
                </Card>
              ),
            },
            {
              key: 'recommendations',
              label: 'Recommendations',
              icon: <BugOutlined />,
              children: (
                <Card title="Cost Optimization Opportunities">
                  {renderRecommendations()}
                </Card>
              ),
            },
          ]}
        />

        <div style={{ marginTop: '24px' }}>
          <Button
            type="primary"
            size="large"
            onClick={() => setShowOptimizationModal(true)}
          >
            Optimize for Budget
          </Button>
        </div>

        <Modal
          title="Optimize for Budget"
          open={showOptimizationModal}
          onCancel={() => setShowOptimizationModal(false)}
          footer={null}
        >
          <Form
            form={budgetForm}
            onFinish={handleOptimizeBudget}
            layout="vertical"
          >
            <Form.Item
              label="Target Monthly Budget ($)"
              name="budget"
              rules={[{ required: true, message: 'Please enter budget' }]}
            >
              <Input
                type="number"
                placeholder="5000"
                prefix="$"
              />
            </Form.Item>
            <Button type="primary" htmlType="submit" block>
              Calculate Optimizations
            </Button>
          </Form>
        </Modal>
      </Spin>
    </div>
  );
};

export default CostAnalysis;
