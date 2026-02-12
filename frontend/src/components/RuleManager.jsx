import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Form, Input, Select, Space, Modal, message, Tag, Switch } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, BugOutlined } from '@ant-design/icons';
import styles from './RuleManager.module.css';

/**
 * RuleManager Component
 * Create, edit, test, and manage automation rules
 * Supports event, time, and condition-based triggers with complex condition logic
 */
const RuleManager = () => {
  const [rules, setRules] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const triggerTypes = [
    { label: 'Event', value: 'event' },
    { label: 'Time (Scheduled)', value: 'time' },
    { label: 'Condition', value: 'condition' },
    { label: 'Data (Record)', value: 'data' },
    { label: 'Webhook', value: 'webhook' },
    { label: 'Manual', value: 'manual' }
  ];

  const conditionOperators = [
    { label: 'Equals', value: 'equals' },
    { label: 'Not Equals', value: 'not_equals' },
    { label: 'Greater Than', value: 'greater_than' },
    { label: 'Less Than', value: 'less_than' },
    { label: 'Contains', value: 'contains' },
    { label: 'In List', value: 'in' },
    { label: 'Exists', value: 'exists' }
  ];

  const actionTypes = [
    { label: 'Send Email', value: 'send_email' },
    { label: 'Send Slack', value: 'send_slack' },
    { label: 'Create Record', value: 'create_record' },
    { label: 'Update Record', value: 'update_record' },
    { label: 'Call API', value: 'call_api' },
    { label: 'Log Event', value: 'log_event' },
    { label: 'Trigger Workflow', value: 'trigger_workflow' },
    { label: 'Send Notification', value: 'send_notification' }
  ];

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/phase10/rules');
      if (response.ok) {
        const data = await response.json();
        setRules(data.rules || []);
      }
    } catch (error) {
      message.error(`Failed to fetch rules: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const openModal = (rule = null) => {
    setEditingRule(rule);
    if (rule) {
      form.setFieldsValue(rule);
    } else {
      form.resetFields();
    }
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingRule(null);
    form.resetFields();
  };

  const saveRule = async (values) => {
    try {
      const url = editingRule
        ? `/api/v1/phase10/rules/${editingRule.id}`
        : '/api/v1/phase10/rules/create';

      const method = editingRule ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values)
      });

      if (response.ok) {
        message.success(`Rule ${editingRule ? 'updated' : 'created'} successfully`);
        fetchRules();
        closeModal();
      }
    } catch (error) {
      message.error(`Failed to save rule: ${error.message}`);
    }
  };

  const deleteRule = async (ruleId) => {
    Modal.confirm({
      title: 'Delete Rule',
      content: 'Are you sure you want to delete this rule?',
      okText: 'Delete',
      okType: 'danger',
      onOk: async () => {
        try {
          const response = await fetch(`/api/v1/phase10/rules/${ruleId}`, {
            method: 'DELETE'
          });

          if (response.ok) {
            message.success('Rule deleted successfully');
            fetchRules();
          }
        } catch (error) {
          message.error(`Failed to delete rule: ${error.message}`);
        }
      }
    });
  };

  const testRule = async (ruleId) => {
    Modal.confirm({
      title: 'Test Rule',
      content: 'Enter test data as JSON:',
      okText: 'Test',
      onOk: async (testData) => {
        try {
          const response = await fetch(`/api/v1/phase10/rules/${ruleId}/test`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(JSON.parse(testData))
          });

          if (response.ok) {
            const result = await response.json();
            message.info(
              `Test Result: Would trigger = ${result.would_trigger}\n` +
              `Conditions: ${result.conditions_count}, Actions: ${result.actions_count}`
            );
          }
        } catch (error) {
          message.error(`Test failed: ${error.message}`);
        }
      }
    });
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      width: 200
    },
    {
      title: 'Trigger Type',
      dataIndex: 'trigger_type',
      key: 'trigger_type',
      render: type => <Tag>{type}</Tag>
    },
    {
      title: 'Status',
      dataIndex: 'is_enabled',
      key: 'is_enabled',
      render: isEnabled => (
        <Tag color={isEnabled ? 'green' : 'red'}>
          {isEnabled ? 'Enabled' : 'Disabled'}
        </Tag>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 300,
      render: (_, record) => (
        <Space size="small">
          <Button
            size="small"
            type="primary"
            icon={<EditOutlined />}
            onClick={() => openModal(record)}
          >
            Edit
          </Button>
          <Button
            size="small"
            icon={<BugOutlined />}
            onClick={() => testRule(record.id)}
          >
            Test
          </Button>
          <Button
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => deleteRule(record.id)}
          >
            Delete
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div className={styles.container}>
      <Card
        title="Automation Rules"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => openModal()}>
            New Rule
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={rules}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title={editingRule ? 'Edit Rule' : 'Create Rule'}
        open={showModal}
        onOk={() => form.submit()}
        onCancel={closeModal}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={saveRule}
        >
          <Form.Item
            label="Rule Name"
            name="name"
            rules={[{ required: true, message: 'Please enter rule name' }]}
          >
            <Input placeholder="Rule name" />
          </Form.Item>

          <Form.Item
            label="Description"
            name="description"
          >
            <Input.TextArea rows={2} placeholder="Rule description" />
          </Form.Item>

          <Form.Item
            label="Trigger Type"
            name="trigger_type"
            rules={[{ required: true }]}
          >
            <Select options={triggerTypes} />
          </Form.Item>

          <Form.Item
            label="Trigger Configuration"
            name={['trigger_config', 'event_type']}
          >
            <Input placeholder="Event type (e.g., customer.created)" />
          </Form.Item>

          <Form.Item label="Conditions">
            <Card size="small" title="Add Conditions">
              <Form.List name="conditions">
                {(fields, { add, remove }) => (
                  <>
                    {fields.map((field) => (
                      <Form.Item key={field.key} wrapperCol={{ span: 24 }}>
                        <Space style={{ width: '100%' }} direction="vertical">
                          <Input
                            placeholder="Field"
                            {...form.getFieldProps([...field.name, 'field'])}
                          />
                          <Select
                            placeholder="Operator"
                            options={conditionOperators}
                            {...form.getFieldProps([...field.name, 'operator'])}
                          />
                          <Input
                            placeholder="Value"
                            {...form.getFieldProps([...field.name, 'value'])}
                          />
                          <Button danger onClick={() => remove(field.name)}>
                            Remove Condition
                          </Button>
                        </Space>
                      </Form.Item>
                    ))}
                    <Button onClick={() => add()}>+ Add Condition</Button>
                  </>
                )}
              </Form.List>
            </Card>
          </Form.Item>

          <Form.Item label="Actions">
            <Card size="small" title="Add Actions">
              <Form.List name="actions">
                {(fields, { add, remove }) => (
                  <>
                    {fields.map((field) => (
                      <Form.Item key={field.key}>
                        <Space style={{ width: '100%' }} direction="vertical">
                          <Select
                            placeholder="Action Type"
                            options={actionTypes}
                            {...form.getFieldProps([...field.name, 'type'])}
                          />
                          <Input.TextArea
                            placeholder="Action Config (JSON)"
                            rows={2}
                            {...form.getFieldProps([...field.name, 'config'])}
                          />
                          <Button danger onClick={() => remove(field.name)}>
                            Remove Action
                          </Button>
                        </Space>
                      </Form.Item>
                    ))}
                    <Button onClick={() => add()}>+ Add Action</Button>
                  </>
                )}
              </Form.List>
            </Card>
          </Form.Item>

          <Form.Item label="Enabled" name="is_enabled" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default RuleManager;
