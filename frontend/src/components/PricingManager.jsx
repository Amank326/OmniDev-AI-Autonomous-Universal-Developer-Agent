/**
 * Phase 16: Pricing Manager Component
 * - Dynamic pricing configuration
 * - Pricing model management
 * - Cost calculation
 */

import React, { useState, useEffect } from 'react';
import { Card, Form, Input, InputNumber, Button, Select, Table, Modal, Spin, message, Row, Col, Statistic, Divider } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, DollarOutlined, CalculatorOutlined } from '@ant-design/icons';

const PricingManager = ({ agentId, userId }) => {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const [tiers, setTiers] = useState([]);
  const [pricing, setPricing] = useState(null);
  const [showTierModal, setShowTierModal] = useState(false);
  const [showCostCalculator, setShowCostCalculator] = useState(false);
  const [editingTier, setEditingTier] = useState(null);
  const [calcInputTokens, setCalcInputTokens] = useState(1000);
  const [calcOutputTokens, setCalcOutputTokens] = useState(1000);
  const [calcResult, setCalcResult] = useState(null);

  useEffect(() => {
    fetchTiers();
    fetchPricing();
  }, [agentId]);

  const fetchTiers = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/agents/${agentId}/tiers`, {
        headers: { 'X-User-ID': userId }
      });
      const data = await response.json();
      setTiers(data.tiers || []);
    } catch (error) {
      message.error('Failed to load tiers');
    } finally {
      setLoading(false);
    }
  };

  const fetchPricing = async () => {
    try {
      const response = await fetch(`/api/v1/agents/${agentId}/pricing`, {
        headers: { 'X-User-ID': userId }
      });
      const data = await response.json();
      setPricing(data);
    } catch (error) {
      console.error('Failed to load pricing');
    }
  };

  const handleCreateTier = async (values) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/agents/${agentId}/tiers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify(values)
      });

      if (response.ok) {
        message.success('Tier created successfully');
        setShowTierModal(false);
        form.resetFields();
        fetchTiers();
      } else {
        message.error('Failed to create tier');
      }
    } catch (error) {
      message.error('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateTier = async (values) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/agents/${agentId}/tiers/${editingTier}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({
          monthly_price: values.monthly_price,
          annual_price: values.annual_price
        })
      });

      if (response.ok) {
        message.success('Tier updated successfully');
        setShowTierModal(false);
        form.resetFields();
        setEditingTier(null);
        fetchTiers();
      } else {
        message.error('Failed to update tier');
      }
    } catch (error) {
      message.error('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCalculateCost = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `/api/v1/agents/${agentId}/calculate-cost`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-User-ID': userId
          },
          body: JSON.stringify({
            input_tokens: calcInputTokens,
            output_tokens: calcOutputTokens
          })
        }
      );
      const data = await response.json();
      setCalcResult(data);
    } catch (error) {
      message.error('Calculation failed');
    } finally {
      setLoading(false);
    }
  };

  const tierColumns = [
    {
      title: 'Tier Name',
      dataIndex: 'name',
      key: 'name'
    },
    {
      title: 'Monthly Price',
      dataIndex: 'monthly_price',
      key: 'monthly_price',
      render: (price) => `$${price.toFixed(2)}`
    },
    {
      title: 'Annual Price',
      dataIndex: 'annual_price',
      key: 'annual_price',
      render: (price) => price ? `$${price.toFixed(2)}` : 'N/A'
    },
    {
      title: 'Monthly Executions',
      dataIndex: 'monthly_executions',
      key: 'monthly_executions',
      render: (val) => val ? val.toLocaleString() : 'Unlimited'
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => {
              setEditingTier(record.id);
              form.setFieldsValue({
                monthly_price: record.monthly_price,
                annual_price: record.annual_price
              });
              setShowTierModal(true);
            }}
          />
          <Button type="link" danger icon={<DeleteOutlined />} />
        </>
      )
    }
  ];

  return (
    <div style={{ padding: '20px' }}>
      <h2>Pricing Configuration</h2>

      {/* Current Pricing */}
      {pricing && (
        <Card title="Current Pricing Model" style={{ marginBottom: '20px' }}>
          <Row gutter={16}>
            <Col xs={24} sm={12} lg={6}>
              <Statistic
                title="Pricing Model"
                value={pricing.pricing_model || 'Tier-based'}
              />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Statistic
                title="Base Price"
                value={pricing.base_price || 0}
                prefix="$"
              />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Statistic
                title="Price/Execution"
                value={pricing.price_per_execution || 0}
                prefix="$"
                precision={4}
              />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Statistic
                title="Price/1K Tokens"
                value={pricing.price_per_1k_input_tokens || 0}
                prefix="$"
                precision={4}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* Tiers Management */}
      <Card title="Pricing Tiers" extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingTier(null);
            form.resetFields();
            setShowTierModal(true);
          }}
        >
          New Tier
        </Button>
      } style={{ marginBottom: '20px' }}>
        <Spin spinning={loading}>
          <Table
            columns={tierColumns}
            dataSource={tiers}
            rowKey="id"
            pagination={false}
          />
        </Spin>
      </Card>

      {/* Cost Calculator */}
      <Card title="Cost Calculator" extra={
        <Button
          icon={<CalculatorOutlined />}
          onClick={() => setShowCostCalculator(!showCostCalculator)}
        >
          Calculate
        </Button>
      }>
        {showCostCalculator && (
          <>
            <Form layout="vertical" style={{ marginBottom: '20px' }}>
              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Form.Item label="Input Tokens">
                    <InputNumber
                      min={0}
                      value={calcInputTokens}
                      onChange={setCalcInputTokens}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item label="Output Tokens">
                    <InputNumber
                      min={0}
                      value={calcOutputTokens}
                      onChange={setCalcOutputTokens}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
              </Row>
              <Button
                type="primary"
                onClick={handleCalculateCost}
                loading={loading}
              >
                Calculate Cost
              </Button>
            </Form>

            {calcResult && (
              <>
                <Divider />
                <Row gutter={16}>
                  <Col xs={24} sm={12} lg={6}>
                    <Statistic
                      title="Input Cost"
                      value={calcResult.input_cost || 0}
                      prefix="$"
                      precision={4}
                    />
                  </Col>
                  <Col xs={24} sm={12} lg={6}>
                    <Statistic
                      title="Output Cost"
                      value={calcResult.output_cost || 0}
                      prefix="$"
                      precision={4}
                    />
                  </Col>
                  <Col xs={24} sm={12} lg={6}>
                    <Statistic
                      title="Total Cost"
                      value={calcResult.total_cost || 0}
                      prefix="$"
                      precision={4}
                      valueStyle={{ color: '#52c41a', fontSize: '20px', fontWeight: 'bold' }}
                    />
                  </Col>
                </Row>
              </>
            )}
          </>
        )}
      </Card>

      {/* Tier Modal */}
      <Modal
        title={editingTier ? 'Edit Tier' : 'Create New Tier'}
        visible={showTierModal}
        onOk={() => form.submit()}
        onCancel={() => {
          setShowTierModal(false);
          setEditingTier(null);
          form.resetFields();
        }}
        loading={loading}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={editingTier ? handleUpdateTier : handleCreateTier}
        >
          {!editingTier && (
            <>
              <Form.Item
                name="name"
                label="Tier Name"
                rules={[{ required: true, message: 'Tier name is required' }]}
              >
                <Input placeholder="e.g., Professional" />
              </Form.Item>

              <Form.Item
                name="monthly_executions"
                label="Monthly Executions"
              >
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </>
          )}

          <Form.Item
            name="monthly_price"
            label="Monthly Price ($)"
            rules={[{ required: true, message: 'Price is required' }]}
          >
            <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="annual_price"
            label="Annual Price ($)"
          >
            <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default PricingManager;
