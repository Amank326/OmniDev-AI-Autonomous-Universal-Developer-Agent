import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Modal, Form, Input, Select, Row, Col,
  Statistic, Tabs, Tag, Space, message, Empty, Spin, Upload,
  Divider, List, Alert
} from 'antd';
import {
  FileTextOutlined, DownloadOutlined, CalculatorOutlined,
  DollarOutlined, CalendarOutlined, CheckCircleOutlined
} from '@ant-design/icons';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as ChartTooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

const TaxReporting = ({ userId, vendorId }) => {
  const [taxYear, setTaxYear] = useState(2026);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  // Mock tax summary data
  const mockTaxSummary = {
    vendor_id: vendorId,
    tax_year: 2026,
    gross_income: 125000.00,
    total_deductions: 28500.00,
    taxable_income: 96500.00,
    estimated_tax_liability: 18620.00,
    deductions_by_category: {
      software: 5200.00,
      equipment: 3500.00,
      supplies: 2800.00,
      professional_fees: 8000.00,
      marketing: 5000.00,
      travel: 4000.00,
    },
    receipts_count: 45,
    tax_forms_generated: ['1099-nec'],
    tax_filing_deadline: '2027-04-15',
    recommended_quarterly_payments: {
      Q1: 4655.00,
      Q2: 4655.00,
      Q3: 4655.00,
      Q4: 4655.00,
    },
  };

  const mock1099Form = {
    doc_id: '1099_123_2026',
    type: '1099-nec',
    tax_year: 2026,
    vendor_name: 'John Developer',
    vendor_ssn: '***-**-1234',
    box_1: 125000.00,
    box_2: 0.00,
    total_payments: 125000.00,
    federal_withheld: 0.00,
    generated_date: '2027-01-15',
    issue_deadline: '2027-01-31',
  };

  const mockQuarterlyEstimate = {
    vendor_id: vendorId,
    ytd_income: 65000.00,
    annualized_income: 125000.00,
    estimated_annual_tax: 18620.00,
    quarterly_payment: 4655.00,
    next_payment_due: '2026-06-15',
    amount_due_this_quarter: 4655.00,
  };

  const deductionData = [
    { category: 'Software', amount: 5200 },
    { category: 'Equipment', amount: 3500 },
    { category: 'Professional Fees', amount: 8000 },
    { category: 'Marketing', amount: 5000 },
    { category: 'Travel', amount: 4000 },
    { category: 'Supplies', amount: 2800 },
  ];

  const handleGenerateTaxSummary = async () => {
    setLoading(true);
    try {
      // Mock API call
      message.success('Tax summary generated successfully');
    } catch (error) {
      message.error('Failed to generate tax summary');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateQuarterly = async () => {
    setLoading(true);
    try {
      // Mock API call
      message.success('Quarterly estimate calculated');
    } catch (error) {
      message.error('Failed to calculate estimate');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload1099 = () => {
    message.info('Downloading 1099-NEC form...');
    // In production: fetch from API: /tax/1099-form
  };

  const handleCreateReceipt = async (values) => {
    setLoading(true);
    try {
      // Mock API call
      message.success('Deduction receipt created');
      form.resetFields();
      setModalVisible(false);
    } catch (error) {
      message.error('Failed to create receipt');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <Card title="Tax Reporting & Deductions" style={{ marginBottom: '20px' }}>
        <Row gutter={16} style={{ marginBottom: '20px' }}>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Gross Income"
              value={mockTaxSummary.gross_income}
              prefix={<DollarOutlined />}
              precision={2}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Total Deductions"
              value={mockTaxSummary.total_deductions}
              prefix={<DollarOutlined />}
              precision={2}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Taxable Income"
              value={mockTaxSummary.taxable_income}
              prefix={<DollarOutlined />}
              precision={2}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Est. Tax Liability"
              value={mockTaxSummary.estimated_tax_liability}
              prefix={<DollarOutlined />}
              precision={2}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Col>
        </Row>

        <Alert
          message="Quarterly Payment Due"
          description={`Next quarterly estimated tax payment of $${mockQuarterlyEstimate.quarterly_payment.toFixed(2)} is due on ${mockQuarterlyEstimate.next_payment_due}`}
          type="warning"
          style={{ marginBottom: '16px' }}
        />

        <Space style={{ marginBottom: '16px' }}>
          <Button 
            type="primary" 
            icon={<CalculatorOutlined />}
            onClick={handleGenerateTaxSummary}
          >
            Recalculate Summary
          </Button>
          <Button 
            type="primary" 
            icon={<CalendarOutlined />}
            onClick={handleGenerateQuarterly}
          >
            Quarterly Estimate
          </Button>
          <Button 
            icon={<DownloadOutlined />}
            onClick={handleDownload1099}
          >
            Download 1099-NEC
          </Button>
        </Space>

        <Tabs>
          {/* TAX SUMMARY TAB */}
          <Tabs.TabPane tab="Tax Summary" key="1">
            <Row gutter={16} style={{ marginBottom: '20px' }}>
              <Col xs={24} sm={12}>
                <Card size="small" title="Tax Calculation">
                  <List size="small">
                    <List.Item>
                      <List.Item.Meta
                        title="Gross Income"
                        description={`$${mockTaxSummary.gross_income.toFixed(2)}`}
                      />
                    </List.Item>
                    <List.Item>
                      <List.Item.Meta
                        title="Standard Deduction"
                        description={`$13,850.00 (or $${mockTaxSummary.total_deductions.toFixed(2)} itemized)`}
                      />
                    </List.Item>
                    <List.Item>
                      <List.Item.Meta
                        title="Taxable Income"
                        description={`$${mockTaxSummary.taxable_income.toFixed(2)}`}
                      />
                    </List.Item>
                    <Divider />
                    <List.Item>
                      <List.Item.Meta
                        title="Estimated Federal Tax"
                        description={`$${mockTaxSummary.estimated_tax_liability.toFixed(2)}`}
                      />
                    </List.Item>
                    <List.Item>
                      <List.Item.Meta
                        title="Effective Tax Rate"
                        description={`${((mockTaxSummary.estimated_tax_liability / mockTaxSummary.gross_income) * 100).toFixed(1)}%`}
                      />
                    </List.Item>
                  </List>
                </Card>
              </Col>
              <Col xs={24} sm={12}>
                <Card size="small" title="Quarterly Payments">
                  <List size="small">
                    {Object.entries(mockTaxSummary.recommended_quarterly_payments).map(([quarter, amount]) => (
                      <List.Item key={quarter}>
                        <List.Item.Meta
                          title={quarter}
                          description={`$${amount.toFixed(2)}`}
                        />
                      </List.Item>
                    ))}
                    <Divider />
                    <List.Item>
                      <List.Item.Meta
                        title="Total Annual Tax"
                        description={`$${mockTaxSummary.estimated_tax_liability.toFixed(2)}`}
                      />
                    </List.Item>
                  </List>
                </Card>
              </Col>
            </Row>
          </Tabs.TabPane>

          {/* DEDUCTIONS TAB */}
          <Tabs.TabPane tab="Deductions" key="2">
            <Button 
              type="primary" 
              onClick={() => setModalVisible(true)}
              style={{ marginBottom: '16px' }}
            >
              Add Deduction Receipt
            </Button>

            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={deductionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <ChartTooltip formatter={(value) => `$${value.toFixed(2)}`} />
                <Bar dataKey="amount" fill="#1890ff" />
              </BarChart>
            </ResponsiveContainer>

            <Table
              style={{ marginTop: '20px' }}
              columns={[
                {
                  title: 'Category',
                  dataIndex: 'category',
                  key: 'category',
                },
                {
                  title: 'Amount',
                  dataIndex: 'amount',
                  key: 'amount',
                  render: (amount) => `$${amount.toFixed(2)}`,
                },
                {
                  title: 'Count',
                  dataIndex: 'count',
                  key: 'count',
                  render: (_, record) => {
                    const categoryCount = mockTaxSummary.receipts_count / Object.keys(mockTaxSummary.deductions_by_category).length;
                    return Math.round(categoryCount);
                  },
                },
              ]}
              dataSource={deductionData.map((item, idx) => ({
                key: idx,
                ...item,
              }))}
              pagination={false}
              size="small"
            />
          </Tabs.TabPane>

          {/* 1099 FORMS TAB */}
          <Tabs.TabPane tab="1099 Forms" key="3">
            <Card title="Form 1099-NEC" type="inner" style={{ marginBottom: '16px' }}>
              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <List size="small">
                    <List.Item>
                      <List.Item.Meta
                        title="Form Type"
                        description="1099-NEC (Non-Employee Compensation)"
                      />
                    </List.Item>
                    <List.Item>
                      <List.Item.Meta
                        title="Tax Year"
                        description={mock1099Form.tax_year}
                      />
                    </List.Item>
                    <List.Item>
                      <List.Item.Meta
                        title="Total Payments (Box 1)"
                        description={`$${mock1099Form.box_1.toFixed(2)}`}
                      />
                    </List.Item>
                    <List.Item>
                      <List.Item.Meta
                        title="Federal Withheld"
                        description={`$${mock1099Form.federal_withheld.toFixed(2)}`}
                      />
                    </List.Item>
                  </List>
                </Col>
                <Col xs={24} sm={12}>
                  <List size="small">
                    <List.Item>
                      <List.Item.Meta
                        title="Generated"
                        description={new Date(mock1099Form.generated_date).toLocaleDateString()}
                      />
                    </List.Item>
                    <List.Item>
                      <List.Item.Meta
                        title="Issue Deadline"
                        description={new Date(mock1099Form.issue_deadline).toLocaleDateString()}
                      />
                    </List.Item>
                    <List.Item>
                      <List.Item.Meta
                        title="Filing Deadline"
                        description="April 15, 2027"
                      />
                    </List.Item>
                    <List.Item>
                      <Button 
                        type="primary" 
                        size="small"
                        onClick={handleDownload1099}
                        icon={<DownloadOutlined />}
                      >
                        Download PDF
                      </Button>
                    </List.Item>
                  </List>
                </Col>
              </Row>
            </Card>

            <Alert
              message="IRS Filing"
              description="Copies of this form must be sent to the IRS by January 31, 2027. This document is required for your tax return."
              type="info"
            />
          </Tabs.TabPane>

          {/* QUARTERLY ESTIMATES TAB */}
          <Tabs.TabPane tab="Quarterly Estimates" key="4">
            <Card title="2026 Estimated Tax Payments" type="inner">
              <Row gutter={16} style={{ marginBottom: '20px' }}>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="YTD Income"
                    value={mockQuarterlyEstimate.ytd_income}
                    prefix="$"
                    precision={2}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="Annualized Income"
                    value={mockQuarterlyEstimate.annualized_income}
                    prefix="$"
                    precision={2}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="Q Payment"
                    value={mockQuarterlyEstimate.quarterly_payment}
                    prefix="$"
                    precision={2}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="Next Due"
                    value={mockQuarterlyEstimate.next_payment_due}
                    prefix={<CalendarOutlined />}
                  />
                </Col>
              </Row>

              <Table
                columns={[
                  { title: 'Quarter', dataIndex: 'quarter', key: 'quarter' },
                  { title: 'Due Date', dataIndex: 'due_date', key: 'due_date' },
                  { title: 'Payment Amount', dataIndex: 'amount', key: 'amount', render: (amount) => `$${amount.toFixed(2)}` },
                  { title: 'Status', dataIndex: 'status', key: 'status', render: (status) => <Tag color={status === 'paid' ? 'green' : 'orange'}>{status.toUpperCase()}</Tag> },
                ]}
                dataSource={[
                  { key: 'Q1', quarter: 'Q1 2026', due_date: '04/15/2026', amount: 4655, status: 'paid' },
                  { key: 'Q2', quarter: 'Q2 2026', due_date: '06/15/2026', amount: 4655, status: 'pending' },
                  { key: 'Q3', quarter: 'Q3 2026', due_date: '09/15/2026', amount: 4655, status: 'pending' },
                  { key: 'Q4', quarter: 'Q4 2026', due_date: '01/15/2027', amount: 4655, status: 'pending' },
                ]}
                pagination={false}
                size="small"
              />
            </Card>
          </Tabs.TabPane>
        </Tabs>
      </Card>

      {/* Add Deduction Modal */}
      <Modal
        title="Add Deduction Receipt"
        visible={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        confirmLoading={loading}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateReceipt}>
          <Form.Item
            label="Category"
            name="category"
            rules={[{ required: true, message: 'Please select category' }]}
          >
            <Select placeholder="Select deduction category">
              <Select.Option value="software">Software</Select.Option>
              <Select.Option value="equipment">Equipment</Select.Option>
              <Select.Option value="supplies">Supplies</Select.Option>
              <Select.Option value="professional_fees">Professional Fees</Select.Option>
              <Select.Option value="marketing">Marketing</Select.Option>
              <Select.Option value="travel">Travel</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            label="Amount"
            name="amount"
            rules={[{ required: true, message: 'Please enter amount' }]}
          >
            <Input type="number" placeholder="0.00" step="0.01" />
          </Form.Item>
          <Form.Item
            label="Description"
            name="description"
          >
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TaxReporting;
