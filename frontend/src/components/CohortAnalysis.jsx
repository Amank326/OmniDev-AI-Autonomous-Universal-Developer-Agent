/**
 * Phase 17: Cohort Analysis Visualization
 * - Retention curves
 * - Revenue trends
 * - Churn analysis by cohort
 */

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Select, Button, Spin, message, Tabs, Tag } from 'antd';
import { LineChart as RechartsLineChart, Line, BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';

const CohortAnalysis = ({ userId }) => {
  const [loading, setLoading] = useState(false);
  const [selectedCohort, setSelectedCohort] = useState('0-30');
  const [cohorts, setCohorts] = useState([]);
  const [retentionCurve, setRetentionCurve] = useState([]);
  const [revenueTrend, setRevenueTrend] = useState([]);
  const [churnMetrics, setChurnMetrics] = useState(null);

  useEffect(() => {
    fetchCohortData();
  }, []);

  const fetchCohortData = async () => {
    try {
      setLoading(true);
      
      // Mock cohort data
      const mockCohorts = [
        {
          cohort_name: "0-30 days",
          member_count: 250,
          churn_rate: 15.2,
          ltv: 450,
          retention_week4: 85
        },
        {
          cohort_name: "31-90 days",
          member_count: 180,
          churn_rate: 8.5,
          ltv: 920,
          retention_week4: 92
        },
        {
          cohort_name: "91-180 days",
          member_count: 120,
          churn_rate: 5.2,
          ltv: 1850,
          retention_week4: 96
        },
        {
          cohort_name: "180+ days",
          member_count: 95,
          churn_rate: 2.1,
          ltv: 3200,
          retention_week4: 98
        }
      ];
      
      setCohorts(mockCohorts);
      
      // Mock retention curve
      const mockRetention = [
        { week: 0, retention_pct: 100 },
        { week: 1, retention_pct: 94 },
        { week: 2, retention_pct: 89 },
        { week: 4, retention_pct: 85 },
        { week: 8, retention_pct: 78 },
        { week: 12, retention_pct: 72 },
        { week: 16, retention_pct: 68 },
        { week: 20, retention_pct: 64 },
        { week: 24, retention_pct: 62 }
      ];
      setRetentionCurve(mockRetention);
      
      // Mock revenue trend
      const mockRevenue = [
        { month: "Jan", revenue: 15000, cohort_0_30: 3000, cohort_31_90: 4500, cohort_91_180: 5000, cohort_180: 2500 },
        { month: "Feb", revenue: 18500, cohort_0_30: 3800, cohort_31_90: 4800, cohort_91_180: 5500, cohort_180: 4400 },
        { month: "Mar", revenue: 22000, cohort_0_30: 4200, cohort_31_90: 5200, cohort_91_180: 6000, cohort_180: 6600 },
        { month: "Apr", revenue: 25600, cohort_0_30: 4800, cohort_31_90: 5800, cohort_91_180: 6800, cohort_180: 8200 }
      ];
      setRevenueTrend(mockRevenue);
      
      setChurnMetrics({
        highest_risk: "0-30 days",
        highest_churn_rate: 15.2,
        best_cohort: "180+ days",
        best_churn_rate: 2.1,
        avg_churn: 7.75
      });
    } catch (error) {
      message.error('Failed to load cohort data');
    } finally {
      setLoading(false);
    }
  };

  const cohortTable = [
    {
      key: '1',
      cohort: "0-30 days",
      members: 250,
      churn_rate: 15.2,
      ltv: 450,
      week4_retention: 85,
      status: "high_risk"
    },
    {
      key: '2',
      cohort: "31-90 days",
      members: 180,
      churn_rate: 8.5,
      ltv: 920,
      week4_retention: 92,
      status: "medium_risk"
    },
    {
      key: '3',
      cohort: "91-180 days",
      members: 120,
      churn_rate: 5.2,
      ltv: 1850,
      week4_retention: 96,
      status: "low_risk"
    },
    {
      key: '4',
      cohort: "180+ days",
      members: 95,
      churn_rate: 2.1,
      ltv: 3200,
      week4_retention: 98,
      status: "stable"
    }
  ];

  const cohortColumns = [
    {
      title: 'Cohort',
      dataIndex: 'cohort',
      key: 'cohort',
      width: 100
    },
    {
      title: 'Members',
      dataIndex: 'members',
      key: 'members',
      width: 80
    },
    {
      title: 'Churn Rate',
      dataIndex: 'churn_rate',
      key: 'churn_rate',
      width: 100,
      render: (rate) => {
        let color = 'green';
        if (rate > 10) color = 'red';
        else if (rate > 5) color = 'orange';
        return <span style={{ color }}>{rate.toFixed(1)}%</span>;
      }
    },
    {
      title: 'Avg LTV',
      dataIndex: 'ltv',
      key: 'ltv',
      width: 100,
      render: (val) => `$${val}`
    },
    {
      title: 'Week 4 Ret.',
      dataIndex: 'week4_retention',
      key: 'week4_retention',
      width: 100,
      render: (val) => `${val}%`
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status) => {
        const colors = {
          high_risk: 'red',
          medium_risk: 'orange',
          low_risk: 'gold',
          stable: 'green'
        };
        const labels = {
          high_risk: 'HIGH RISK',
          medium_risk: 'MEDIUM RISK',
          low_risk: 'LOW RISK',
          stable: 'STABLE'
        };
        return <Tag color={colors[status]}>{labels[status]}</Tag>;
      }
    }
  ];

  return (
    <div style={{ padding: '20px' }}>
      <h2>Cohort Analysis & Lifecycle Tracking</h2>

      {/* Key Metrics Overview */}
      <Row gutter={16} style={{ marginBottom: '20px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Cohorts"
              value={cohorts.length}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Highest Risk"
              value={churnMetrics?.highest_churn_rate || 0}
              suffix="%"
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Best Performing"
              value={churnMetrics?.best_churn_rate || 0}
              suffix="%"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Avg LTV"
              value={1350}
              prefix="$"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Cohort Comparison Table */}
      <Card title="Cohort Comparison" style={{ marginBottom: '20px' }}>
        <Spin spinning={loading}>
          <Table
            columns={cohortColumns}
            dataSource={cohortTable}
            pagination={false}
            scroll={{ x: 800 }}
          />
        </Spin>
      </Card>

      {/* Retention Curve */}
      <Card title="📊 Retention Curve" style={{ marginBottom: '20px' }}>
        <Spin spinning={loading}>
          {retentionCurve.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <RechartsLineChart data={retentionCurve}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="week" label={{ value: 'Weeks', position: 'insideBottomRight', offset: -5 }} />
                <YAxis label={{ value: 'Retention %', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="retention_pct"
                  stroke="#52c41a"
                  name="Retention Rate"
                  dot={{ fill: '#52c41a' }}
                />
              </RechartsLineChart>
            </ResponsiveContainer>
          ) : null}
        </Spin>
      </Card>

      {/* Revenue Trend by Cohort */}
      <Card title="💰 Revenue Trend by Cohort" style={{ marginBottom: '20px' }}>
        <Spin spinning={loading}>
          {revenueTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={350}>
              <RechartsBarChart data={revenueTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
                <Legend />
                <Bar dataKey="cohort_0_30" stackId="a" fill="#f5222d" name="0-30 days" />
                <Bar dataKey="cohort_31_90" stackId="a" fill="#fa8c16" name="31-90 days" />
                <Bar dataKey="cohort_91_180" stackId="a" fill="#faad14" name="91-180 days" />
                <Bar dataKey="cohort_180" stackId="a" fill="#52c41a" name="180+ days" />
              </RechartsBarChart>
            </ResponsiveContainer>
          ) : null}
        </Spin>
      </Card>

      {/* Churn Analysis */}
      <Card title="⚠️ Churn Analysis" style={{ marginBottom: '20px' }}>
        <Spin spinning={loading}>
          <Tabs>
            <Tabs.TabPane tab="By Cohort" key="1">
              <ResponsiveContainer width="100%" height={300}>
                <RechartsBarChart data={cohortTable}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="cohort" />
                  <YAxis />
                  <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
                  <Legend />
                  <Bar dataKey="churn_rate" fill="#f5222d" name="Churn Rate %" />
                </RechartsBarChart>
              </ResponsiveContainer>
            </Tabs.TabPane>
            <Tabs.TabPane tab="Risk Assessment" key="2">
              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <h4>🔴 Highest Risk Cohort</h4>
                  <p><strong>0-30 days:</strong> 15.2% churn rate</p>
                  <p><strong>Members:</strong> 250 users</p>
                  <p><strong>MRR at Risk:</strong> $3,750</p>
                  <Button type="primary" danger>Launch Intervention</Button>
                </Col>
                <Col xs={24} md={12}>
                  <h4>🟢 Best Performing Cohort</h4>
                  <p><strong>180+ days:</strong> 2.1% churn rate</p>
                  <p><strong>Members:</strong> 95 users</p>
                  <p><strong>LTV:</strong> $3,200</p>
                  <Button type="primary">Learn Best Practices</Button>
                </Col>
              </Row>
            </Tabs.TabPane>
          </Tabs>
        </Spin>
      </Card>

      {/* Insights & Recommendations */}
      <Card title="🎯 Insights & Recommendations">
        <h4>Key Findings:</h4>
        <ul>
          <li>✓ New cohorts (0-30 days) have 7x higher churn than mature cohorts (180+ days)</li>
          <li>✓ Week 4 is critical checkpoint: retention drops from 100% to 85%</li>
          <li>✓ LTV increases 7x from first month to second year ($450 → $3,200)</li>
          <li>✓ Revenue per cohort stable once past 90-day mark</li>
        </ul>

        <h4>Recommended Actions:</h4>
        <ol>
          <li>Improve onboarding for 0-30 day cohort (target: 85% → 95% week 4 retention)</li>
          <li>Implement 7-day and 14-day check-ins for new users</li>
          <li>Create "90-day success" milestone campaign</li>
          <li>Analyze best practices from 180+ day cohort and apply to new users</li>
          <li>A/B test pricing for early-stage cohorts to reduce churn</li>
        </ol>
      </Card>
    </div>
  );
};

export default CohortAnalysis;
