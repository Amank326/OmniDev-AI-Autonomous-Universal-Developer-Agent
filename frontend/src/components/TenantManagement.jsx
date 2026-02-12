/**
 * Phase 12: TenantManagement Component
 * Tenant administration interface
 */

import React, { useState, useEffect } from 'react';
import {
  Tabs, Table, Button, Modal, Form, Input, Select, Card, Statistic,
  Space, Tag, Drawer, message, Popconfirm, Row, Col, Divider
} from 'antd';
import {
  PlusOutlined, DeleteOutlined, EditOutlined, UserAddOutlined,
  DownloadOutlined, WarningOutlined
} from '@ant-design/icons';

const TenantManagement = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editDrawerVisible, setEditDrawerVisible] = useState(false);
  const [membersDrawerVisible, setMembersDrawerVisible] = useState(false);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();

  // Load tenants
  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/enterprise/tenants', {
        headers: {
          'x-user-id': localStorage.getItem('userId'),
          'x-tenant-id': localStorage.getItem('tenantId'),
        }
      });
      const data = await response.json();
      setTenants(data.tenants || []);
    } catch (error) {
      message.error('Failed to load tenants');
    }
    setLoading(false);
  };

  const handleCreateTenant = async (values) => {
    try {
      const response = await fetch('/api/v1/enterprise/tenants', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-user-id': localStorage.getItem('userId'),
          'x-tenant-id': localStorage.getItem('tenantId'),
        },
        body: JSON.stringify(values)
      });

      if (response.ok) {
        message.success('Tenant created successfully');
        setCreateModalVisible(false);
        form.resetFields();
        loadTenants();
      }
    } catch (error) {
      message.error('Failed to create tenant');
    }
  };

  const handleUpdateTenant = async (tenantId, values) => {
    try {
      const response = await fetch(`/api/v1/enterprise/tenants/${tenantId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'x-user-id': localStorage.getItem('userId'),
          'x-tenant-id': localStorage.getItem('tenantId'),
        },
        body: JSON.stringify(values)
      });

      if (response.ok) {
        message.success('Tenant updated');
        setEditDrawerVisible(false);
        loadTenants();
      }
    } catch (error) {
      message.error('Failed to update tenant');
    }
  };

  const handleDeleteTenant = async (tenantId) => {
    try {
      const response = await fetch(`/api/v1/enterprise/tenants/${tenantId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'x-user-id': localStorage.getItem('userId'),
          'x-tenant-id': localStorage.getItem('tenantId'),
        },
        body: JSON.stringify({ reason: 'Requested by admin' })
      });

      if (response.ok) {
        message.success('Tenant deleted');
        loadTenants();
      }
    } catch (error) {
      message.error('Failed to delete tenant');
    }
  };

  const tenantColumns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text) => <strong>{text}</strong>
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Members',
      dataIndex: 'member_count',
      key: 'member_count',
      render: (count) => <span>{count}</span>
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleDateString()
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<EditOutlined />}
            onClick={() => {
              setSelectedTenant(record);
              editForm.setFieldsValue(record);
              setEditDrawerVisible(true);
            }}
          >
            Edit
          </Button>
          <Button
            type="primary"
            ghost
            size="small"
            icon={<UserAddOutlined />}
            onClick={() => {
              setSelectedTenant(record);
              setMembersDrawerVisible(true);
            }}
          >
            Members
          </Button>
          <Popconfirm
            title="Delete tenant?"
            description="This action cannot be undone"
            onConfirm={() => handleDeleteTenant(record.id)}
            okText="Delete"
            okType="danger"
            cancelText="Cancel"
          >
            <Button danger size="small" icon={<DeleteOutlined />}>
              Delete
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title="Tenant Management"
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
          Create Tenant
        </Button>}
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* Overview Tab */}
          <Tabs.TabPane label="Overview" key="overview">
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="Total Tenants"
                  value={tenants.length}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="Active"
                  value={tenants.filter(t => t.status === 'active').length}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="Total Members"
                  value={tenants.reduce((sum, t) => sum + t.member_count, 0)}
                  valueStyle={{ color: '#faad14' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="Created This Month"
                  value={tenants.filter(t => {
                    const created = new Date(t.created_at);
                    const now = new Date();
                    return created.getMonth() === now.getMonth();
                  }).length}
                />
              </Col>
            </Row>
          </Tabs.TabPane>

          {/* Tenants List Tab */}
          <Tabs.TabPane label="All Tenants" key="list">
            <Table
              columns={tenantColumns}
              dataSource={tenants}
              loading={loading}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Tabs.TabPane>

          {/* Active Tenants Tab */}
          <Tabs.TabPane label="Active" key="active">
            <Table
              columns={tenantColumns}
              dataSource={tenants.filter(t => t.status === 'active')}
              loading={loading}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Tabs.TabPane>

          {/* Suspended Tenants Tab */}
          <Tabs.TabPane label="Suspended" key="suspended">
            <Table
              columns={tenantColumns}
              dataSource={tenants.filter(t => t.status !== 'active')}
              loading={loading}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Tabs.TabPane>

          {/* Settings Tab */}
          <Tabs.TabPane label="Settings" key="settings">
            <Card title="Default Settings" style={{ marginBottom: '16px' }}>
              <Form layout="vertical">
                <Form.Item label="Default Plan" name="defaultPlan">
                  <Select placeholder="Select default plan">
                    <Select.Option value="free">Free</Select.Option>
                    <Select.Option value="starter">Starter</Select.Option>
                    <Select.Option value="professional">Professional</Select.Option>
                  </Select>
                </Form.Item>
                <Form.Item label="Default Data Residency" name="defaultResidency">
                  <Select placeholder="Select default residency">
                    <Select.Option value="US">United States</Select.Option>
                    <Select.Option value="EU">Europe</Select.Option>
                    <Select.Option value="APAC">Asia-Pacific</Select.Option>
                    <Select.Option value="CA">Canada</Select.Option>
                  </Select>
                </Form.Item>
                <Button type="primary">Save Settings</Button>
              </Form>
            </Card>
          </Tabs.TabPane>
        </Tabs>
      </Card>

      {/* Create Tenant Modal */}
      <Modal
        title="Create New Tenant"
        open={createModalVisible}
        onOk={() => form.submit()}
        onCancel={() => setCreateModalVisible(false)}
        okText="Create"
      >
        <Form form={form} layout="vertical" onFinish={handleCreateTenant}>
          <Form.Item name="tenant_name" label="Tenant Name" rules={[{ required: true }]}>
            <Input placeholder="Enter tenant name" />
          </Form.Item>
          <Form.Item name="plan" label="Plan" initialValue="free">
            <Select>
              <Select.Option value="free">Free</Select.Option>
              <Select.Option value="starter">Starter ($29/mo)</Select.Option>
              <Select.Option value="professional">Professional ($99/mo)</Select.Option>
              <Select.Option value="enterprise">Enterprise (Custom)</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="data_residency" label="Data Residency" initialValue="US">
            <Select>
              <Select.Option value="US">United States</Select.Option>
              <Select.Option value="EU">Europe</Select.Option>
              <Select.Option value="APAC">Asia-Pacific</Select.Option>
              <Select.Option value="CA">Canada</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit Tenant Drawer */}
      <Drawer
        title="Edit Tenant"
        placement="right"
        onClose={() => setEditDrawerVisible(false)}
        open={editDrawerVisible}
        footer={
          <Space style={{ float: 'right' }}>
            <Button onClick={() => setEditDrawerVisible(false)}>Cancel</Button>
            <Button
              type="primary"
              onClick={() => {
                editForm.submit();
                setEditDrawerVisible(false);
              }}
            >
              Save
            </Button>
          </Space>
        }
      >
        {selectedTenant && (
          <Form
            form={editForm}
            layout="vertical"
            onFinish={(values) => handleUpdateTenant(selectedTenant.id, values)}
          >
            <Form.Item label="Tenant ID">
              <Input value={selectedTenant.id} disabled />
            </Form.Item>
            <Form.Item name="name" label="Name">
              <Input />
            </Form.Item>
            <Form.Item name="data_residency" label="Data Residency">
              <Select>
                <Select.Option value="US">United States</Select.Option>
                <Select.Option value="EU">Europe</Select.Option>
                <Select.Option value="APAC">Asia-Pacific</Select.Option>
                <Select.Option value="CA">Canada</Select.Option>
              </Select>
            </Form.Item>
            <Divider />
            <Statistic title="Created" value={new Date(selectedTenant.created_at).toLocaleString()} />
            <Statistic title="Members" value={selectedTenant.member_count} />
          </Form>
        )}
      </Drawer>

      {/* Members Management Drawer */}
      <Drawer
        title="Manage Members"
        placement="right"
        onClose={() => setMembersDrawerVisible(false)}
        open={membersDrawerVisible}
        width={600}
      >
        {selectedTenant && (
          <Card title={`Members of ${selectedTenant.name}`}>
            <Form layout="vertical">
              <Form.Item label="Add Member Email">
                <Space.Compact style={{ width: '100%' }}>
                  <Input placeholder="user@example.com" />
                  <Button type="primary">Add</Button>
                </Space.Compact>
              </Form.Item>
            </Form>
            <Divider />
            <Table
              columns={[
                { title: 'User', dataIndex: 'email', key: 'email' },
                { title: 'Role', dataIndex: 'role', key: 'role' },
                {
                  title: 'Actions',
                  render: () => (
                    <Button type="link" danger size="small">Remove</Button>
                  )
                }
              ]}
              dataSource={[]}
              pagination={false}
            />
          </Card>
        )}
      </Drawer>
    </div>
  );
};

export default TenantManagement;
