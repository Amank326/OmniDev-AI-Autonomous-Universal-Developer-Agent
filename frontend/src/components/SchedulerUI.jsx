import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Form, Input, Select, Space, Modal, message, Tag, Switch, TimePicker } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ClockCircleOutlined } from '@ant-design/icons';
import styles from './SchedulerUI.module.css';
import dayjs from 'dayjs';

/**
 * SchedulerUI Component
 * Manage cron-based scheduled tasks with timezone support
 * Create, edit, and monitor scheduled workflow and automation execution
 */
const SchedulerUI = () => {
  const [tasks, setTasks] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const commonCronExpressions = [
    { label: 'Every minute', value: '* * * * *' },
    { label: 'Every 5 minutes', value: '*/5 * * * *' },
    { label: 'Every hour', value: '0 * * * *' },
    { label: 'Daily (9 AM)', value: '0 9 * * *' },
    { label: 'Weekly (Monday 9 AM)', value: '0 9 * * 1' },
    { label: 'Monthly (1st, 9 AM)', value: '0 9 1 * *' },
    { label: 'Every business day', value: '0 9 * * 1-5' }
  ];

  const timezones = [
    'UTC', 'America/New_York', 'America/Los_Angeles', 'Europe/London',
    'Europe/Paris', 'Asia/Tokyo', 'Asia/Shanghai', 'Australia/Sydney'
  ];

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/phase10/scheduler/tasks');
      if (response.ok) {
        const data = await response.json();
        setTasks(data.tasks || []);
      }
    } catch (error) {
      message.error(`Failed to fetch tasks: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const openModal = (task = null) => {
    setEditingTask(task);
    if (task) {
      form.setFieldsValue({
        ...task,
        next_execution: task.next_execution ? dayjs(task.next_execution) : null
      });
    } else {
      form.resetFields();
    }
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingTask(null);
    form.resetFields();
  };

  const saveTask = async (values) => {
    try {
      const url = editingTask
        ? `/api/v1/phase10/scheduler/${editingTask.id}`
        : '/api/v1/phase10/scheduler/create';

      const method = editingTask ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values)
      });

      if (response.ok) {
        message.success(`Task ${editingTask ? 'updated' : 'created'} successfully`);
        fetchTasks();
        closeModal();
      }
    } catch (error) {
      message.error(`Failed to save task: ${error.message}`);
    }
  };

  const deleteTask = async (taskId) => {
    Modal.confirm({
      title: 'Delete Task',
      content: 'Are you sure you want to delete this scheduled task?',
      okText: 'Delete',
      okType: 'danger',
      onOk: async () => {
        try {
          const response = await fetch(`/api/v1/phase10/scheduler/${taskId}`, {
            method: 'DELETE'
          });

          if (response.ok) {
            message.success('Task deleted successfully');
            fetchTasks();
          }
        } catch (error) {
          message.error(`Failed to delete task: ${error.message}`);
        }
      }
    });
  };

  const toggleTask = async (taskId, isEnabled) => {
    try {
      const response = await fetch(`/api/v1/phase10/scheduler/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_enabled: !isEnabled })
      });

      if (response.ok) {
        message.success(`Task ${!isEnabled ? 'enabled' : 'disabled'}`);
        fetchTasks();
      }
    } catch (error) {
      message.error(`Failed to update task: ${error.message}`);
    }
  };

  const columns = [
    {
      title: 'Task Name',
      dataIndex: 'name',
      key: 'name',
      width: 200
    },
    {
      title: 'Cron Expression',
      dataIndex: 'cron_expression',
      key: 'cron_expression',
      render: expr => <code>{expr}</code>
    },
    {
      title: 'Timezone',
      dataIndex: 'timezone',
      key: 'timezone'
    },
    {
      title: 'Status',
      dataIndex: 'is_enabled',
      key: 'is_enabled',
      render: (isEnabled) => (
        <Tag color={isEnabled ? 'green' : 'red'}>
          {isEnabled ? 'Enabled' : 'Disabled'}
        </Tag>
      )
    },
    {
      title: 'Next Execution',
      dataIndex: 'next_execution',
      key: 'next_execution',
      render: (time) => {
        if (!time) return '-';
        return new Date(time).toLocaleString();
      }
    },
    {
      title: 'Last Run',
      dataIndex: 'last_execution',
      key: 'last_execution',
      render: (time) => {
        if (!time) return '-';
        return new Date(time).toLocaleString();
      }
    },
    {
      title: 'Success Rate',
      key: 'success_rate',
      width: 150,
      render: (_, record) => {
        if (record.total_executions === 0) return '0%';
        const rate = (record.successful_executions / record.total_executions * 100).toFixed(1);
        return `${rate}%`;
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 350,
      render: (_, record) => (
        <Space size="small">
          <Button
            size="small"
            type={record.is_enabled ? 'primary' : 'default'}
            onClick={() => toggleTask(record.id, record.is_enabled)}
          >
            {record.is_enabled ? 'Disable' : 'Enable'}
          </Button>
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
            danger
            icon={<DeleteOutlined />}
            onClick={() => deleteTask(record.id)}
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
        title={
          <span>
            <ClockCircleOutlined style={{ marginRight: '8px' }} />
            Scheduled Tasks
          </span>
        }
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => openModal()}>
            New Task
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          size="small"
        />
      </Card>

      <Modal
        title={editingTask ? 'Edit Scheduled Task' : 'Create Scheduled Task'}
        open={showModal}
        onOk={() => form.submit()}
        onCancel={closeModal}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={saveTask}
        >
          <Form.Item
            label="Task Name"
            name="name"
            rules={[{ required: true, message: 'Please enter task name' }]}
          >
            <Input placeholder="Task name" />
          </Form.Item>

          <Form.Item
            label="Description"
            name="description"
          >
            <Input.TextArea rows={2} placeholder="Task description" />
          </Form.Item>

          <Form.Item
            label="Cron Expression"
            name="cron_expression"
            rules={[{ required: true, message: 'Please enter cron expression' }]}
          >
            <Select
              placeholder="Select or enter cron expression"
              options={commonCronExpressions}
              filterOption={false}
            />
          </Form.Item>

          <div style={{
            padding: '12px',
            backgroundColor: '#f0f2f5',
            borderRadius: '4px',
            marginBottom: '16px',
            fontSize: '12px'
          }}>
            <strong>Cron Format:</strong> minute hour day_of_month month day_of_week<br />
            Examples: <code>0 9 * * *</code> (Daily 9 AM), <code>*/5 * * * *</code> (Every 5 min)
          </div>

          <Form.Item
            label="Timezone"
            name="timezone"
            initialValue="UTC"
          >
            <Select options={timezones.map(tz => ({ label: tz, value: tz }))} />
          </Form.Item>

          <Form.Item
            label="Linked Workflow"
            name="workflow_id"
          >
            <Input placeholder="Workflow ID (optional)" />
          </Form.Item>

          <Form.Item label="Retry Settings">
            <Space>
              <Form.Item
                label="Max Retries"
                name="max_retries"
                initialValue={3}
                style={{ marginBottom: 0 }}
              >
                <Input type="number" style={{ width: '100px' }} />
              </Form.Item>
              <Form.Item
                label="Retry Delay (sec)"
                name="retry_delay"
                initialValue={300}
                style={{ marginBottom: 0 }}
              >
                <Input type="number" style={{ width: '120px' }} />
              </Form.Item>
            </Space>
          </Form.Item>

          <Form.Item label="Enabled" name="is_enabled" valuePropName="checked" initialValue={true}>
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SchedulerUI;
