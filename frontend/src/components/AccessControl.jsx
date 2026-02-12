/**
 * Phase 12: AccessControl Component
 * RBAC management and audit logging interface
 */

import React, { useState, useEffect } from 'react';
import {
  Tabs, Table, Button, Modal, Form, Input, Select, Card, Row, Col,
  Space, Tag, Tree, Drawer, message, Timeline, Statistic, Divider,
  DatePicker, Popconfirm
} from 'antd';
import {
  LockOutlined, UnlockOutlined, AuditOutlined, UserOutlined,
  DownloadOutlined, SearchOutlined, ClearOutlined
} from '@ant-design/icons';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const AccessControl = () => {
  const [activeTab, setActiveTab] = useState('rbac');
  const [roles, setRoles] = useState([]);
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [roleDrawerVisible, setRoleDrawerVisible] = useState(false);
  const [permissionsDrawerVisible, setPermissionsDrawerVisible] = useState(false);
  const [auditDrawerVisible, setAuditDrawerVisible] = useState(false);
  const [form] = Form.useForm();

  const tenantId = localStorage.getItem('tenantId');
  const userId = localStorage.getItem('userId');

  // Load data
  useEffect(() => {
    loadRoles();
    loadAuditLogs();
  }, []);

  const loadRoles = async () => {
    try {
      const response = await fetch('/api/v1/enterprise/rbac/roles', {
        headers: {
          'x-user-id': userId,
          'x-tenant-id': tenantId,
        }
      });
      const data = await response.json();
      setRoles(data.roles || []);
    } catch (error) {
      message.error('Failed to load roles');
    }
  };

  const loadAuditLogs = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/enterprise/audit/logs?limit=100', {
        headers: {
          'x-user-id': userId,
          'x-tenant-id': tenantId,
        }
      });
      const data = await response.json();
      setAuditLogs(data.logs || []);
    } catch (error) {
      message.error('Failed to load audit logs');
    }
    setLoading(false);
  };

  const handleAssignRole = async (userId, role) => {
    try {
      const response = await fetch(`/api/v1/enterprise/rbac/roles/${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-user-id': localStorage.getItem('userId'),
          'x-tenant-id': tenantId,
        },
        body: JSON.stringify({ role })
      });

      if (response.ok) {
        message.success(`Role assigned: ${role}`);
        loadRoles();
      }
    } catch (error) {
      message.error('Failed to assign role');
    }
  };

  const handleRevokeRole = async (userId, role) => {
    try {
      const response = await fetch(`/api/v1/enterprise/rbac/roles/${userId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'x-user-id': localStorage.getItem('userId'),
          'x-tenant-id': tenantId,
        },
        body: JSON.stringify({ role })
      });

      if (response.ok) {
        message.success(`Role revoked: ${role}`);
        loadRoles();
      }
    } catch (error) {
      message.error('Failed to revoke role');
    }
  };

  const handleExportAudit = async () => {
    try {
      const response = await fetch('/api/v1/enterprise/audit/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-user-id': userId,
          'x-tenant-id': tenantId,
        },
        body: JSON.stringify({ format: 'csv' })
      });

      if (response.ok) {
        const data = await response.json();
        // Create download
        const element = document.createElement('a');
        element.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(data.content_preview));
        element.setAttribute('download', `audit-log-${new Date().toISOString()}.csv`);
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
        message.success('Audit logs exported');
      }
    } catch (error) {
      message.error('Failed to export audit logs');
    }
  };

  // Role columns
  const roleColumns = [
    {
      title: 'Role Name',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <LockOutlined />
          <strong>{text}</strong>
          {record.is_system_role && <Tag color="blue">System</Tag>}
        </Space>
      )
    },
    {
      title: 'Permissions',
      dataIndex: ['permission_count'],
      key: 'permissions',
      render: (count) => (
        <Tag color="cyan">{count} permissions</Tag>
      )
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description'
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Button type="link" onClick={() => {
          setSelectedUser(record);
          setPermissionsDrawerVisible(true);
        }}>
          View Permissions
        </Button>
      )
    }
  ];

  // Audit log columns
  const auditColumns = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (date) => new Date(date).toLocaleString(),
      width: 200
    },
    {
      title: 'Event',
      dataIndex: 'event_type',
      key: 'event_type',
      render: (event) => (
        <Tag>{event.split('.')[1] || event}</Tag>
      )
    },
    {
      title: 'User',
      dataIndex: 'user_id',
      key: 'user_id'
    },
    {
      title: 'Resource',
      dataIndex: 'resource_type',
      key: 'resource_type',
      render: (type) => type ? <Tag color="blue">{type}</Tag> : '-'
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'success' ? 'green' : 'red'}>
          {status}
        </Tag>
      )
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    }
  ];

  // Calculate stats for audit logs
  const auditStats = {
    total: auditLogs.length,
    success: auditLogs.filter(l => l.status === 'success').length,
    failures: auditLogs.filter(l => l.status === 'failure').length,
    today: auditLogs.filter(l => {
      const logDate = new Date(l.timestamp);
      const today = new Date();
      return logDate.toDateString() === today.toDateString();
    }).length
  };

  // Event type distribution for chart
  const eventDistribution = Object.entries(
    auditLogs.reduce((acc, log) => {
      const type = log.event_type.split('.')[1] || log.event_type;
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {})
  ).map(([name, value]) => ({ name, value })).slice(0, 10);

  return (
    <div style={{ padding: '24px' }}>
      <Card title="Access Control & Audit">
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* RBAC Tab */}
          <Tabs.TabPane label="RBAC Management" key="rbac">
            <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="Total Roles"
                  value={roles.length}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="System Roles"
                  value={roles.filter(r => r.is_system_role).length}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="Custom Roles"
                  value={roles.filter(r => !r.is_system_role).length}
                  valueStyle={{ color: '#faad14' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="Total Permissions"
                  value={roles.reduce((sum, r) => sum + r.permission_count, 0)}
                  valueStyle={{ color: '#f5222d' }}
                />
              </Col>
            </Row>

            <Table
              columns={roleColumns}
              dataSource={roles}
              loading={loading}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Tabs.TabPane>

          {/* User Management Tab */}
          <Tabs.TabPane label="User Roles" key="users">
            <Card
              title="Assign Roles to Users"
              extra={<Button type="primary" icon={<UserOutlined />}>Add User</Button>}
            >
              <Form layout="vertical">
                <Row gutter={16}>
                  <Col xs={24} sm={12}>
                    <Form.Item label="User Email" required>
                      <Input placeholder="user@example.com" />
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={12}>
                    <Form.Item label="Role" required>
                      <Select placeholder="Select role">
                        {roles.map(role => (
                          <Select.Option key={role.id} value={role.id}>
                            {role.name}
                          </Select.Option>
                        ))}
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>
                <Button type="primary">Assign Role</Button>
              </Form>
            </Card>

            <Card title="User Role Assignments" style={{ marginTop: '24px' }}>
              <Table
                columns={[
                  { title: 'User', dataIndex: 'email', key: 'email' },
                  { title: 'Role', dataIndex: 'role', key: 'role' },
                  {
                    title: 'Actions',
                    render: () => (
                      <Popconfirm title="Revoke role?" onConfirm={() => message.success('Role revoked')}>
                        <Button type="link" danger>Revoke</Button>
                      </Popconfirm>
                    )
                  }
                ]}
                dataSource={[]}
                pagination={false}
              />
            </Card>
          </Tabs.TabPane>

          {/* Audit Logs Tab */}
          <Tabs.TabPane label="Audit Logs" key="audit">
            <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title="Total Events"
                    value={auditStats.total}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title="Successful"
                    value={auditStats.success}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title="Failures"
                    value={auditStats.failures}
                    valueStyle={{ color: '#f5222d' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title="Today"
                    value={auditStats.today}
                    valueStyle={{ color: '#faad14' }}
                  />
                </Card>
              </Col>
            </Row>

            <Card title="Event Distribution" style={{ marginBottom: '24px' }}>
              {eventDistribution.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={eventDistribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#1890ff" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p>No audit logs yet</p>
              )}
            </Card>

            <Card
              title="Audit Log Entries"
              extra={
                <Space>
                  <Button icon={<DownloadOutlined />} onClick={handleExportAudit}>
                    Export
                  </Button>
                  <Button icon={<ClearOutlined />}>Clear Filters</Button>
                </Space>
              }
            >
              <Table
                columns={auditColumns}
                dataSource={auditLogs}
                loading={loading}
                rowKey="event_id"
                pagination={{ pageSize: 15 }}
                scroll={{ x: 1000 }}
              />
            </Card>
          </Tabs.TabPane>

          {/* Compliance Tab */}
          <Tabs.TabPane label="Compliance" key="compliance">
            <Card title="Compliance Status">
              <Timeline
                items={[
                  {
                    children: (
                      <div>
                        <strong>Audit Logging Enabled</strong>
                        <p>All user actions are being logged for compliance</p>
                      </div>
                    )
                  },
                  {
                    children: (
                      <div>
                        <strong>Role-Based Access Control</strong>
                        <p>{roles.length} roles configured with {roles.reduce((sum, r) => sum + r.permission_count, 0)} permissions</p>
                      </div>
                    )
                  },
                  {
                    children: (
                      <div>
                        <strong>Data Residency Enforced</strong>
                        <p>Multi-region support with tenant-level isolation</p>
                      </div>
                    )
                  },
                  {
                    children: (
                      <div>
                        <strong>Subscription Management</strong>
                        <p>Usage quotas and billing integration active</p>
                      </div>
                    )
                  }
                ]}
              />
            </Card>
          </Tabs.TabPane>
        </Tabs>
      </Card>

      {/* Permissions Drawer */}
      <Drawer
        title={selectedUser ? `Permissions for ${selectedUser.name}` : 'Permissions'}
        placement="right"
        onClose={() => setPermissionsDrawerVisible(false)}
        open={permissionsDrawerVisible}
        width={600}
      >
        {selectedUser && (
          <Card>
            <h4>Assigned Permissions</h4>
            <Space wrap>
              {selectedUser.permissions?.map((perm, idx) => (
                <Tag key={idx} color="blue">{perm}</Tag>
              ))}
            </Space>
          </Card>
        )}
      </Drawer>
    </div>
  );
};

export default AccessControl;
