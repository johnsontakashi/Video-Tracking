import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Tag,
  Space,
  Input,
  Select,
  Modal,
  Form,
  message,
  Avatar,
  Switch,
  Dropdown,
  Menu,
  Badge,
  Tooltip,
  DatePicker
} from 'antd';
import {
  UserOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  SearchOutlined,
  MoreOutlined,
  CrownOutlined,
  SafetyCertificateOutlined,
  UserSwitchOutlined,
  MailOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
// Using native Date functions instead of moment
import './UserManagement.css';

const { Option } = Select;

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  username?: string;
  role: string;
  is_active: boolean;
  email_verified: boolean;
  current_plan: string;
  created_at: string;
  last_login?: string;
}

const roleColors = {
  admin: '#f50',
  analyst: '#1890ff',
  guest: '#87d068'
};

const roleLabels = {
  admin: 'Admin',
  analyst: 'Analyst',
  guest: 'User'
};

const planColors = {
  free: '#52c41a',
  starter: '#1890ff',
  professional: '#722ed1',
  enterprise: '#fa8c16'
};

// Helper function for relative time
const getRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 0) return `${diffDays} days ago`;
  if (diffHours > 0) return `${diffHours} hours ago`;
  if (diffMinutes > 0) return `${diffMinutes} minutes ago`;
  return 'Just now';
};

const UserManagement: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [searchText, setSearchText] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [form] = Form.useForm();

  useEffect(() => {
    fetchUsers();
  }, []);

  const getMockUsers = (): User[] => [
    {
      id: 1,
      email: 'admin@videotracking.com',
      first_name: 'Admin',
      last_name: 'User',
      full_name: 'Admin User',
      username: 'admin',
      role: 'admin',
      is_active: true,
      email_verified: true,
      current_plan: 'enterprise',
      created_at: '2024-01-15T10:30:00Z',
      last_login: '2024-01-21T14:30:00Z'
    },
    {
      id: 2,
      email: 'analyst@company.com',
      first_name: 'Data',
      last_name: 'Analyst',
      full_name: 'Data Analyst',
      username: 'analyst',
      role: 'analyst',
      is_active: true,
      email_verified: true,
      current_plan: 'professional',
      created_at: '2024-01-18T09:15:00Z',
      last_login: '2024-01-21T13:45:00Z'
    },
    {
      id: 3,
      email: 'guest@example.com',
      first_name: 'Guest',
      last_name: 'User',
      full_name: 'Guest User',
      username: 'guest',
      role: 'guest',
      is_active: true,
      email_verified: false,
      current_plan: 'starter',
      created_at: '2024-01-20T16:20:00Z',
      last_login: '2024-01-21T12:10:00Z'
    },
    {
      id: 4,
      email: 'inactive@example.com',
      first_name: 'Inactive',
      last_name: 'User',
      full_name: 'Inactive User',
      role: 'guest',
      is_active: false,
      email_verified: true,
      current_plan: 'free',
      created_at: '2024-01-10T11:00:00Z'
    }
  ];

  const fetchUsers = async () => {
    try {
      setLoading(true);
      
      // Check if we should use mock data
      const useMockData = process.env.REACT_APP_USE_MOCK_DATA === 'true' || 
                         process.env.NODE_ENV === 'development';
      
      if (useMockData) {
        console.log('Using mock users data');
        // Simulate loading time
        await new Promise(resolve => setTimeout(resolve, 500));
        setUsers(getMockUsers());
        return;
      }
      
      // Try to fetch from backend
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${process.env.REACT_APP_API_URL || ''}/api/users`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.users) {
        setUsers(data.users.map((user: any) => ({
          ...user,
          full_name: user.full_name || `${user.first_name} ${user.last_name}`
        })));
      } else {
        console.warn('No users data in response, using mock data');
        setUsers(getMockUsers());
      }
    } catch (error) {
      console.warn('Failed to fetch users from backend, using mock data:', error);
      setUsers(getMockUsers());
    } finally {
      setLoading(false);
    }
  };

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    form.setFieldsValue(user);
    setIsModalVisible(true);
  };

  const handleAddUser = () => {
    setEditingUser(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleSubmit = async (values: any) => {
    try {
      const token = localStorage.getItem('access_token');
      const method = editingUser ? 'PUT' : 'POST';
      const url = editingUser 
        ? `/api/users/${editingUser.id}`
        : '/api/users';

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(values)
      });

      const data = await response.json();
      
      if (data.success) {
        message.success(
          editingUser 
            ? 'User updated successfully' 
            : 'User created successfully'
        );
        setIsModalVisible(false);
        fetchUsers();
      } else {
        message.error(data.message || 'Operation failed');
      }
    } catch (error) {
      console.error('Error saving user:', error);
      message.error('Failed to save user');
    }
  };

  const handleToggleStatus = async (userId: number, currentStatus: boolean) => {
    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`/api/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_active: !currentStatus })
      });

      const data = await response.json();
      
      if (data.success) {
        message.success(
          `User ${!currentStatus ? 'activated' : 'deactivated'} successfully`
        );
        fetchUsers();
      } else {
        message.error('Failed to update user status');
      }
    } catch (error) {
      console.error('Error updating user status:', error);
      message.error('Failed to update user status');
    }
  };

  const getActionMenuItems = (user: User) => [
    {
      key: 'edit',
      icon: <EditOutlined />,
      label: 'Edit User',
      onClick: () => handleEditUser(user)
    },
    {
      key: 'toggle',
      icon: <UserSwitchOutlined />,
      label: `${user.is_active ? 'Deactivate' : 'Activate'} User`,
      onClick: () => handleToggleStatus(user.id, user.is_active)
    },
    {
      type: 'divider' as const
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: 'Delete User',
      danger: true,
      onClick: () => {
        Modal.confirm({
          title: 'Delete User',
          content: `Are you sure you want to delete ${user.full_name}?`,
          okText: 'Delete',
          okType: 'danger',
          onOk: () => {
            message.info('Delete functionality coming soon');
          }
        });
      }
    }
  ];

  const filteredUsers = users.filter(user => {
    const matchesSearch = !searchText || 
      user.full_name.toLowerCase().includes(searchText.toLowerCase()) ||
      user.email.toLowerCase().includes(searchText.toLowerCase()) ||
      (user.username && user.username.toLowerCase().includes(searchText.toLowerCase()));
    
    const matchesRole = !roleFilter || user.role === roleFilter;
    const matchesStatus = !statusFilter || 
      (statusFilter === 'active' && user.is_active) ||
      (statusFilter === 'inactive' && !user.is_active);
    
    return matchesSearch && matchesRole && matchesStatus;
  });

  const columns = [
    {
      title: 'User',
      key: 'user',
      render: (record: User) => (
        <div className="user-info">
          <Avatar
            size={40}
            icon={<UserOutlined />}
            style={{ 
              backgroundColor: record.is_active ? '#87d068' : '#ccc' 
            }}
          />
          <div className="user-details">
            <div className="user-name">
              {record.full_name}
              {record.role === 'admin' && (
                <CrownOutlined 
                  style={{ color: '#faad14', marginLeft: 8 }} 
                  title="Admin"
                />
              )}
            </div>
            <div className="user-email">{record.email}</div>
            {record.username && (
              <div className="user-username">@{record.username}</div>
            )}
          </div>
        </div>
      )
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <Tag color={roleColors[role as keyof typeof roleColors]}>
          {roleLabels[role as keyof typeof roleLabels]}
        </Tag>
      ),
      filters: [
        { text: 'Admin', value: 'admin' },
        { text: 'Analyst', value: 'analyst' },
        { text: 'User', value: 'guest' }
      ],
      onFilter: (value: any, record: User) => record.role === value
    },
    {
      title: 'Plan',
      dataIndex: 'current_plan',
      key: 'plan',
      render: (plan: string) => (
        <Tag color={planColors[plan as keyof typeof planColors]}>
          {plan.charAt(0).toUpperCase() + plan.slice(1)}
        </Tag>
      )
    },
    {
      title: 'Status',
      key: 'status',
      render: (record: User) => (
        <div className="status-info">
          <Badge
            status={record.is_active ? 'success' : 'default'}
            text={record.is_active ? 'Active' : 'Inactive'}
          />
          {record.email_verified && (
            <Tooltip title="Email Verified">
              <MailOutlined 
                style={{ color: '#52c41a', marginLeft: 8 }} 
              />
            </Tooltip>
          )}
        </div>
      )
    },
    {
      title: 'Last Login',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (lastLogin: string) => (
        lastLogin ? (
          <Tooltip title={new Date(lastLogin).toLocaleString()}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <CalendarOutlined />
              {getRelativeTime(lastLogin)}
            </span>
          </Tooltip>
        ) : (
          <span style={{ color: '#ccc' }}>Never</span>
        )
      ),
      sorter: (a: User, b: User) => {
        if (!a.last_login && !b.last_login) return 0;
        if (!a.last_login) return 1;
        if (!b.last_login) return -1;
        return new Date(a.last_login).getTime() - new Date(b.last_login).getTime();
      }
    },
    {
      title: 'Joined',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => (
        <Tooltip title={new Date(date).toLocaleString()}>
          {new Date(date).toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: '2-digit' 
          })}
        </Tooltip>
      ),
      sorter: (a: User, b: User) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: User) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditUser(record)}
          />
          <Switch
            size="small"
            checked={record.is_active}
            onChange={() => handleToggleStatus(record.id, record.is_active)}
            disabled={record.id === currentUser?.id}
          />
          <Dropdown 
            menu={{ items: getActionMenuItems(record) }}
            trigger={['click']}
            placement="bottomRight"
          >
            <Button
              type="text"
              icon={<MoreOutlined />}
              disabled={record.id === currentUser?.id}
            />
          </Dropdown>
        </Space>
      )
    }
  ];

  return (
    <div className="user-management">
      <Card
        title={
          <div className="page-header">
            <h2>User Management</h2>
            <span className="subtitle">Manage user accounts and permissions</span>
          </div>
        }
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAddUser}
          >
            Add User
          </Button>
        }
      >
        <div className="filters-section">
          <Space size="middle" wrap>
            <Input
              placeholder="Search users..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 300 }}
              prefix={<SearchOutlined />}
            />
            <Select
              placeholder="Filter by role"
              style={{ width: 150 }}
              value={roleFilter}
              onChange={setRoleFilter}
              allowClear
            >
              <Option value="admin">Admin</Option>
              <Option value="analyst">Analyst</Option>
              <Option value="guest">User</Option>
            </Select>
            <Select
              placeholder="Filter by status"
              style={{ width: 150 }}
              value={statusFilter}
              onChange={setStatusFilter}
              allowClear
            >
              <Option value="active">Active</Option>
              <Option value="inactive">Inactive</Option>
            </Select>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={filteredUsers}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `Total ${total} users`
          }}
          scroll={{ x: 900 }}
        />
      </Card>

      <Modal
        title={editingUser ? 'Edit User' : 'Add New User'}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          className="user-form"
        >
          <div className="form-row">
            <Form.Item
              label="First Name"
              name="first_name"
              rules={[{ required: true, message: 'First name is required' }]}
              style={{ width: '48%' }}
            >
              <Input placeholder="Enter first name" />
            </Form.Item>

            <Form.Item
              label="Last Name"
              name="last_name"
              rules={[{ required: true, message: 'Last name is required' }]}
              style={{ width: '48%' }}
            >
              <Input placeholder="Enter last name" />
            </Form.Item>
          </div>

          <Form.Item
            label="Email"
            name="email"
            rules={[
              { required: true, message: 'Email is required' },
              { type: 'email', message: 'Please enter a valid email' }
            ]}
          >
            <Input placeholder="Enter email address" />
          </Form.Item>

          <Form.Item
            label="Username"
            name="username"
          >
            <Input placeholder="Enter username (optional)" />
          </Form.Item>

          <div className="form-row">
            <Form.Item
              label="Role"
              name="role"
              rules={[{ required: true, message: 'Role is required' }]}
              style={{ width: '48%' }}
            >
              <Select placeholder="Select role">
                <Option value="guest">
                  <UserOutlined /> User
                </Option>
                <Option value="analyst">
                  <SafetyCertificateOutlined /> Analyst
                </Option>
                <Option value="admin">
                  <CrownOutlined /> Admin
                </Option>
              </Select>
            </Form.Item>

            <Form.Item
              label="Status"
              name="is_active"
              valuePropName="checked"
              style={{ width: '48%' }}
            >
              <Switch 
                checkedChildren="Active" 
                unCheckedChildren="Inactive"
              />
            </Form.Item>
          </div>

          {!editingUser && (
            <Form.Item
              label="Password"
              name="password"
              rules={[
                { required: true, message: 'Password is required' },
                { min: 8, message: 'Password must be at least 8 characters' }
              ]}
            >
              <Input.Password placeholder="Enter password" />
            </Form.Item>
          )}

          <div className="form-actions">
            <Space>
              <Button onClick={() => setIsModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                {editingUser ? 'Update' : 'Create'} User
              </Button>
            </Space>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default UserManagement;