import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Modal, Form, Input, Select, DatePicker,
  Statistic, Row, Col, Tabs, Tag, Space, Tooltip, message, Empty,
  Upload, Spin
} from 'antd';
import {
  FileOutlined, DownloadOutlined, PaymentOutlined, PlusOutlined,
  CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined,
  DollarOutlined, HistoryOutlined
} from '@ant-design/icons';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as ChartTooltip, Legend, ResponsiveContainer } from 'recharts';

const InvoiceManager = ({ agentId, userId }) => {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [paymentModalVisible, setPaymentModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [paymentForm] = Form.useForm();

  // Mock data
  const mockInvoices = [
    {
      id: 'inv_1001',
      invoice_number: 'INV-1001',
      amount: 2500.00,
      currency: 'USD',
      status: 'paid',
      issued_date: '2026-01-15',
      due_date: '2026-02-14',
      amount_paid: 2500.00,
      payment_method: 'credit_card',
      description: 'Agent Marketplace Services - January 2026'
    },
    {
      id: 'inv_1002',
      invoice_number: 'INV-1002',
      amount: 3000.00,
      currency: 'USD',
      status: 'partially_paid',
      issued_date: '2026-02-01',
      due_date: '2026-03-03',
      amount_paid: 1500.00,
      payment_method: null,
      description: 'Agent Marketplace Services - February 2026'
    },
    {
      id: 'inv_1003',
      invoice_number: 'INV-1003',
      amount: 2800.00,
      currency: 'USD',
      status: 'issued',
      issued_date: '2026-02-07',
      due_date: '2026-03-09',
      amount_paid: 0.00,
      payment_method: null,
      description: 'Agent Marketplace Services - March 2026'
    },
  ];

  const paymentMetrics = {
    total_invoiced: 8300.00,
    total_paid: 4000.00,
    collection_rate: 48.19,
    total_overdue: 1500.00,
    average_payment_days: 12,
    invoices_issued: 3,
    invoices_paid: 1,
  };

  useEffect(() => {
    setInvoices(mockInvoices);
  }, [agentId]);

  const statusColors = {
    draft: 'default',
    issued: 'processing',
    sent: 'processing',
    viewed: 'processing',
    partially_paid: 'warning',
    paid: 'success',
    overdue: 'error',
    cancelled: 'default',
  };

  const statusIcons = {
    paid: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
    partially_paid: <ClockCircleOutlined style={{ color: '#faad14' }} />,
    issued: <FileOutlined style={{ color: '#1890ff' }} />,
    overdue: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
  };

  const handleCreateInvoice = async (values) => {
    setLoading(true);
    try {
      // Mock API call
      const newInvoice = {
        id: `inv_${Date.now()}`,
        invoice_number: `INV-${1004}`,
        amount: values.amount,
        currency: values.currency || 'USD',
        status: 'draft',
        issued_date: new Date().toISOString().split('T')[0],
        due_date: values.due_date?.format('YYYY-MM-DD'),
        amount_paid: 0,
        description: values.description,
      };
      setInvoices([...invoices, newInvoice]);
      message.success('Invoice created successfully');
      form.resetFields();
      setIsModalVisible(false);
    } catch (error) {
      message.error('Failed to create invoice');
    } finally {
      setLoading(false);
    }
  };

  const handleRecordPayment = async (values) => {
    setLoading(true);
    try {
      // Mock API call
      const updated = invoices.map(inv => {
        if (inv.id === selectedInvoice.id) {
          const newAmountPaid = (inv.amount_paid || 0) + values.amount_paid;
          return {
            ...inv,
            amount_paid: newAmountPaid,
            status: newAmountPaid >= inv.amount ? 'paid' : 'partially_paid',
            payment_method: values.payment_method,
          };
        }
        return inv;
      });
      setInvoices(updated);
      message.success('Payment recorded successfully');
      paymentForm.resetFields();
      setPaymentModalVisible(false);
    } catch (error) {
      message.error('Failed to record payment');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = (invoice) => {
    message.info(`Downloading PDF for invoice ${invoice.invoice_number}`);
    // In production, fetch from API: /invoices/{id}/pdf
  };

  const columns = [
    {
      title: 'Invoice #',
      dataIndex: 'invoice_number',
      key: 'invoice_number',
      render: (text, record) => (
        <a onClick={() => {
          setSelectedInvoice(record);
          setPaymentModalVisible(true);
        }}>
          {text}
        </a>
      ),
    },
    {
      title: 'Amount',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount, record) => `${record.currency} ${amount.toFixed(2)}`,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={statusColors[status]} icon={statusIcons[status]}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Paid',
      dataIndex: 'amount_paid',
      key: 'amount_paid',
      render: (paid, record) => `${record.currency} ${paid.toFixed(2)}`,
    },
    {
      title: 'Due Date',
      dataIndex: 'due_date',
      key: 'due_date',
      render: (date) => new Date(date).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="Download PDF">
            <Button 
              type="text" 
              icon={<DownloadOutlined />}
              onClick={() => handleDownloadPDF(record)}
            />
          </Tooltip>
          <Button 
            type="primary" 
            size="small"
            onClick={() => {
              setSelectedInvoice(record);
              setPaymentModalVisible(true);
            }}
            disabled={record.status === 'paid'}
          >
            Record Payment
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '20px' }}>
      <Card title="Invoice Management" style={{ marginBottom: '20px' }}>
        <Row gutter={16} style={{ marginBottom: '20px' }}>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Total Invoiced"
              value={paymentMetrics.total_invoiced}
              prefix={<DollarOutlined />}
              precision={2}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Total Paid"
              value={paymentMetrics.total_paid}
              precision={2}
              suffix={`(${paymentMetrics.collection_rate.toFixed(1)}%)`}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Outstanding"
              value={paymentMetrics.total_invoiced - paymentMetrics.total_paid}
              precision={2}
              valueStyle={{ color: paymentMetrics.total_overdue > 0 ? '#ff4d4f' : '#1890ff' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Avg Payment Time"
              value={paymentMetrics.average_payment_days}
              suffix="days"
            />
          </Col>
        </Row>

        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => setIsModalVisible(true)}
          style={{ marginBottom: '16px' }}
        >
          Create Invoice
        </Button>

        <Table 
          columns={columns} 
          dataSource={invoices}
          loading={loading}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Create Invoice Modal */}
      <Modal
        title="Create Invoice"
        visible={isModalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
        }}
        confirmLoading={loading}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateInvoice}>
          <Form.Item
            label="Amount"
            name="amount"
            rules={[{ required: true, message: 'Please enter amount' }]}
          >
            <Input type="number" placeholder="0.00" step="0.01" />
          </Form.Item>
          <Form.Item
            label="Currency"
            name="currency"
            initialValue="USD"
          >
            <Select>
              <Select.Option value="USD">USD</Select.Option>
              <Select.Option value="EUR">EUR</Select.Option>
              <Select.Option value="GBP">GBP</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            label="Due Date"
            name="due_date"
            rules={[{ required: true, message: 'Please select due date' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            label="Description"
            name="description"
          >
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Record Payment Modal */}
      <Modal
        title={`Record Payment - ${selectedInvoice?.invoice_number}`}
        visible={paymentModalVisible}
        onOk={() => paymentForm.submit()}
        onCancel={() => {
          setPaymentModalVisible(false);
          paymentForm.resetFields();
        }}
        confirmLoading={loading}
      >
        {selectedInvoice && (
          <>
            <Form form={paymentForm} layout="vertical" onFinish={handleRecordPayment}>
              <Form.Item label="Invoice Amount">
                <Input disabled value={`USD ${selectedInvoice.amount.toFixed(2)}`} />
              </Form.Item>
              <Form.Item label="Already Paid">
                <Input disabled value={`USD ${selectedInvoice.amount_paid.toFixed(2)}`} />
              </Form.Item>
              <Form.Item label="Remaining">
                <Input 
                  disabled 
                  value={`USD ${(selectedInvoice.amount - selectedInvoice.amount_paid).toFixed(2)}`}
                />
              </Form.Item>
              <Form.Item
                label="Payment Amount"
                name="amount_paid"
                rules={[{ required: true, message: 'Please enter payment amount' }]}
              >
                <Input 
                  type="number" 
                  placeholder="0.00" 
                  step="0.01"
                  max={selectedInvoice.amount - selectedInvoice.amount_paid}
                />
              </Form.Item>
              <Form.Item
                label="Payment Method"
                name="payment_method"
                rules={[{ required: true, message: 'Please select payment method' }]}
              >
                <Select>
                  <Select.Option value="credit_card">Credit Card</Select.Option>
                  <Select.Option value="bank_transfer">Bank Transfer</Select.Option>
                  <Select.Option value="check">Check</Select.Option>
                </Select>
              </Form.Item>
            </Form>
          </>
        )}
      </Modal>
    </div>
  );
};

export default InvoiceManager;
