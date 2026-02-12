/**
 * Phase 16: Agent Billing Components
 * - Subscription management
 * - Payment method handling
 * - Tier selection
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Form, Modal, Select, InputNumber, Spin, message, Table, Tag, Space, Statistic, Row, Col } from 'antd';
import { CreditCardOutlined, DollarOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';

const AgentBilling = ({ agentId, userId, onPaymentComplete }) => {
  const [loading, setLoading] = useState(false);
  const [tiers, setTiers] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [selectedTier, setSelectedTier] = useState(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState(null);
  const [billingCycle, setBillingCycle] = useState('monthly');

  useEffect(() => {
    fetchTiers();
    fetchSubscriptions();
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
      message.error('Failed to load pricing tiers');
    } finally {
      setLoading(false);
    }
  };

  const fetchSubscriptions = async () => {
    try {
      const response = await fetch('/api/v1/agents/subscriptions', {
        headers: { 'X-User-ID': userId }
      });
      const data = await response.json();
      const agentSubs = data.subscriptions.filter(s => s.agent_id === agentId);
      setSubscriptions(agentSubs);
    } catch (error) {
      console.error('Failed to load subscriptions');
    }
  };

  const handleSubscribe = async () => {
    if (!selectedTier || !paymentMethod) {
      message.warning('Please select a tier and payment method');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`/api/v1/agents/${agentId}/subscribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({
          tier_id: selectedTier,
          billing_cycle: billingCycle,
          payment_method_id: paymentMethod
        })
      });

      if (response.ok) {
        const data = await response.json();
        message.success('Subscription created successfully!');
        setShowPaymentModal(false);
        fetchSubscriptions();
        onPaymentComplete?.();
      } else {
        message.error('Failed to create subscription');
      }
    } catch (error) {
      message.error('Subscription error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelSubscription = async (subscriptionId) => {
    Modal.confirm({
      title: 'Cancel Subscription',
      content: 'Are you sure you want to cancel this subscription?',
      onOk: async () => {
        try {
          setLoading(true);
          await fetch(`/api/v1/agents/subscriptions/${subscriptionId}`, {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
              'X-User-ID': userId
            },
            body: JSON.stringify({ status: 'cancelled' })
          });
          message.success('Subscription cancelled');
          fetchSubscriptions();
        } catch (error) {
          message.error('Failed to cancel subscription');
        } finally {
          setLoading(false);
        }
      }
    });
  };

  const subscriptionColumns = [
    {
      title: 'Tier',
      dataIndex: 'tier_id',
      key: 'tier_id'
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status?.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Cycle',
      dataIndex: 'billing_cycle',
      key: 'billing_cycle'
    },
    {
      title: 'Monthly Amount',
      dataIndex: 'monthly_amount',
      key: 'monthly_amount',
      render: (amount) => `$${amount.toFixed(2)}`
    },
    {
      title: 'Renewal',
      dataIndex: 'renewal_date',
      key: 'renewal_date',
      render: (date) => new Date(date).toLocaleDateString()
    },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <Button danger size="small" onClick={() => handleCancelSubscription(record.id)}>
          Cancel
        </Button>
      )
    }
  ];

  return (
    <div style={{ padding: '20px' }}>
      <h2>Billing & Subscriptions</h2>

      {/* Current Subscriptions */}
      <Card title="Current Subscriptions" style={{ marginBottom: '20px' }}>
        <Spin spinning={loading}>
          {subscriptions.length > 0 ? (
            <Table
              columns={subscriptionColumns}
              dataSource={subscriptions}
              rowKey="id"
              pagination={false}
            />
          ) : (
            <p>No active subscriptions</p>
          )}
        </Spin>
      </Card>

      {/* Available Tiers */}
      <Card title="Available Plans" style={{ marginBottom: '20px' }}>
        <Spin spinning={loading}>
          <Row gutter={[16, 16]}>
            {tiers.map(tier => (
              <Col xs={24} sm={12} lg={8} key={tier.id}>
                <Card
                  hoverable
                  onClick={() => {
                    setSelectedTier(tier.id);
                    setShowPaymentModal(true);
                  }}
                  style={{
                    border: selectedTier === tier.id ? '2px solid #1890ff' : '1px solid #d9d9d9',
                    cursor: 'pointer'
                  }}
                >
                  <h3>{tier.name}</h3>
                  <Statistic
                    prefix="$"
                    value={tier.monthly_price}
                    suffix="/month"
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold' }}
                  />
                  <div style={{ marginTop: '16px' }}>
                    <p><CheckCircleOutlined /> {tier.monthly_executions?.toLocaleString() || 'Unlimited'} Executions</p>
                    <p><CheckCircleOutlined /> {tier.monthly_tokens?.toLocaleString() || 'Unlimited'} Tokens</p>
                    {tier.features && tier.features.map((feature, idx) => (
                      <p key={idx}><CheckCircleOutlined /> {feature}</p>
                    ))}
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </Spin>
      </Card>

      {/* Payment Modal */}
      <Modal
        title="Complete Subscription"
        visible={showPaymentModal}
        onOk={handleSubscribe}
        onCancel={() => setShowPaymentModal(false)}
        loading={loading}
      >
        <Form layout="vertical">
          <Form.Item label="Billing Cycle">
            <Select
              value={billingCycle}
              onChange={setBillingCycle}
              options={[
                { label: 'Monthly', value: 'monthly' },
                { label: 'Annual', value: 'annual' }
              ]}
            />
          </Form.Item>

          <Form.Item label="Payment Method">
            <Select
              placeholder="Select payment method"
              value={paymentMethod}
              onChange={setPaymentMethod}
              options={[
                { label: 'Credit Card', value: 'credit_card' },
                { label: 'PayPal', value: 'paypal' },
                { label: 'Bank Transfer', value: 'bank_transfer' }
              ]}
            />
          </Form.Item>

          {selectedTier && (
            <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
              <p><strong>Selected Plan:</strong> {tiers.find(t => t.id === selectedTier)?.name}</p>
              <p><strong>Price:</strong> ${(tiers.find(t => t.id === selectedTier)?.[billingCycle === 'annual' ? 'annual_price' : 'monthly_price'] || 0).toFixed(2)} / {billingCycle}</p>
            </div>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default AgentBilling;
