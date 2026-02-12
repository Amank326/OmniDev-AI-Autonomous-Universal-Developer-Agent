/**
 * Phase 16: Revenue Analytics Dashboard
 * - Sales metrics and trends
 * - Monthly/yearly reports
 * - Revenue visualization
 */

import React, { useState, useEffect } from 'react';
import { Card, Statistic, Row, Col, LineChart, BarChart, Select, Spin, message, Table, Tag } from 'antd';
import { DollarOutlined, ShoppingCartOutlined, UserOutlined, TrendingUpOutlined } from '@ant-design/icons';
import { LineChart as RechartsLineChart, Line, BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const RevenueAnalytics = ({ agentId, userId }) => {
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [trends, setTrends] = useState([]);
  const [monthlyReport, setMonthlyReport] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState('30');
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));

  useEffect(() => {
    fetchMetrics();
    fetchTrends();
    fetchMonthlyReport();
  }, [agentId, selectedPeriod]);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `/api/v1/agents/${agentId}/sales-metrics?days=${selectedPeriod}`,
        { headers: { 'X-User-ID': userId } }
      );
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      message.error('Failed to load metrics');
    } finally {
      setLoading(false);
    }
  };

  const fetchTrends = async () => {
    try {
      const response = await fetch(
        `/api/v1/agents/${agentId}/revenue-trends?days=${selectedPeriod}`,
        { headers: { 'X-User-ID': userId } }
      );
      const data = await response.json();
      setTrends(data.trends || []);
    } catch (error) {
      console.error('Failed to load trends');
    }
  };

  const fetchMonthlyReport = async () => {
    try {
      const response = await fetch(
        `/api/v1/agents/${agentId}/monthly-report/${selectedMonth}`,
        { headers: { 'X-User-ID': userId } }
      );
      const data = await response.json();
      setMonthlyReport(data);
    } catch (error) {
      console.error('Failed to load monthly report');
    }
  };

  const transactionColumns = [
    {
      title: 'Date',
      dataIndex: 'date',
      key: 'date',
      render: (date) => new Date(date).toLocaleDateString()
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type) => <Tag>{type}</Tag>
    },
    {
      title: 'Amount',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount) => `$${amount.toFixed(2)}`
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'completed' ? 'green' : 'orange'}>
          {status?.toUpperCase()}
        </Tag>
      )
    }
  ];

  return (
    <div style={{ padding: '20px' }}>
      <h2>Revenue Analytics</h2>

      {/* Period Selection */}
      <Card style={{ marginBottom: '20px' }}>
        <Row gutter={16}>
          <Col xs={24} sm={12}>
            <Select
              style={{ width: '100%' }}
              value={selectedPeriod}
              onChange={setSelectedPeriod}
              options={[
                { label: 'Last 7 days', value: '7' },
                { label: 'Last 30 days', value: '30' },
                { label: 'Last 90 days', value: '90' },
                { label: 'Last 365 days', value: '365' }
              ]}
            />
          </Col>
          <Col xs={24} sm={12}>
            <Select
              style={{ width: '100%' }}
              value={selectedMonth}
              onChange={setSelectedMonth}
              placeholder="Select month"
            />
          </Col>
        </Row>
      </Card>

      {/* Key Metrics */}
      <Spin spinning={loading}>
        <Row gutter={16} style={{ marginBottom: '20px' }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Total Revenue"
                value={metrics?.total_revenue || 0}
                prefix="$"
                precision={2}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Total Sales"
                value={metrics?.total_sales || 0}
                suffix="transactions"
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Active Subscriptions"
                value={metrics?.active_subscriptions || 0}
                prefix={<UserOutlined />}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Avg Transaction"
                value={metrics?.avg_transaction || 0}
                prefix="$"
                precision={2}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>
      </Spin>

      {/* Revenue Trend Chart */}
      <Card title="Revenue Trend" style={{ marginBottom: '20px' }}>
        <Spin spinning={loading}>
          {trends.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <RechartsLineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="revenue"
                  stroke="#52c41a"
                  dot={{ fill: '#52c41a' }}
                  name="Revenue"
                />
                <Line
                  type="monotone"
                  dataKey="transactions"
                  stroke="#1890ff"
                  dot={{ fill: '#1890ff' }}
                  name="Transactions"
                />
              </RechartsLineChart>
            </ResponsiveContainer>
          ) : (
            <p>No trend data available</p>
          )}
        </Spin>
      </Card>

      {/* Monthly Report */}
      {monthlyReport && (
        <Card title={`Monthly Report - ${selectedMonth}`} style={{ marginBottom: '20px' }}>
          <Row gutter={16}>
            <Col xs={24} sm={12} lg={6}>
              <Statistic
                title="Month Revenue"
                value={monthlyReport.total_revenue || 0}
                prefix="$"
                precision={2}
              />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Statistic
                title="New Subscriptions"
                value={monthlyReport.new_subscriptions || 0}
              />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Statistic
                title="Churn Rate"
                value={monthlyReport.churn_rate || 0}
                suffix="%"
                precision={1}
              />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Statistic
                title="Pending Payout"
                value={monthlyReport.pending_payout || 0}
                prefix="$"
                precision={2}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* Transactions Table */}
      <Card title="Recent Transactions">
        <Spin spinning={loading}>
          {monthlyReport?.transactions && monthlyReport.transactions.length > 0 ? (
            <Table
              columns={transactionColumns}
              dataSource={monthlyReport.transactions}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          ) : (
            <p>No transactions</p>
          )}
        </Spin>
      </Card>
    </div>
  );
};

export default RevenueAnalytics;
