import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Card, Row, Col, Button, Table, Modal, Form, Input, Select, message, Tabs } from 'antd';
import {
  UserOutlined,
  SettingOutlined,
  DatabaseOutlined,
  BarChartOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  LogoutOutlined,
  DashboardOutlined
} from '@ant-design/icons';
import PolitikosLogo, { PolitikosLogoText } from '../Brand/PolitikosLogo';
import './AdminDashboard.css';

// const { TabPane } = Tabs; // Deprecated - using items API instead
const { Option } = Select;

// Mock data for demonstration
const mockUsers = [
  { id: 1, email: 'admin@videotracking.com', role: 'admin', status: 'active', lastLogin: '2024-01-15' },
  { id: 2, email: 'test@example.com', role: 'guest', status: 'active', lastLogin: '2024-01-14' },
  { id: 3, email: 'analyst@company.com', role: 'analyst', status: 'active', lastLogin: '2024-01-13' },
];

const mockInfluencers = [
  { id: 1, username: '@techguru123', platform: 'Instagram', followers: 125000, status: 'active' },
  { id: 2, username: '@lifestyle_blogger', platform: 'YouTube', followers: 89000, status: 'active' },
  { id: 3, username: '@fitness_influencer', platform: 'TikTok', followers: 156000, status: 'pending' },
];

const AdminDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [isUserModalVisible, setIsUserModalVisible] = useState(false);
  const [isInfluencerModalVisible, setIsInfluencerModalVisible] = useState(false);
  const [form] = Form.useForm();

  const handleLogout = async () => {
    try {
      await logout();
      message.success('Logged out successfully');
    } catch (error) {
      console.error('Logout failed:', error);
      message.error('Logout failed');
    }
  };

  const userColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <span className={`role-tag ${role}`}>{role.toUpperCase()}</span>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <span className={`status-badge ${status}`}>
          {status === 'active' ? '✅' : '❌'} {status}
        </span>
      ),
    },
    {
      title: 'Last Login',
      dataIndex: 'lastLogin',
      key: 'lastLogin',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: () => (
        <div>
          <Button icon={<EditOutlined />} size="small" style={{ marginRight: 8 }}>
            Edit
          </Button>
          <Button icon={<DeleteOutlined />} size="small" danger>
            Delete
          </Button>
        </div>
      ),
    },
  ];

  const influencerColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Username',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: 'Platform',
      dataIndex: 'platform',
      key: 'platform',
    },
    {
      title: 'Followers',
      dataIndex: 'followers',
      key: 'followers',
      render: (followers: number) => followers.toLocaleString(),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <span className={`status-badge ${status}`}>
          {status === 'active' ? '✅' : '⏳'} {status}
        </span>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: () => (
        <div>
          <Button icon={<EditOutlined />} size="small" style={{ marginRight: 8 }}>
            Edit
          </Button>
          <Button icon={<DeleteOutlined />} size="small" danger>
            Delete
          </Button>
        </div>
      ),
    },
  ];

  const handleAddUser = () => {
    setIsUserModalVisible(true);
  };

  const handleAddInfluencer = () => {
    setIsInfluencerModalVisible(true);
  };

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <div className="admin-dashboard">
      <header className="admin-header">
        <div className="admin-header-left">
          <PolitikosLogoText size="large" className="admin-logo" />
          <div className="admin-title">
            <h1>Painel Administrativo</h1>
            <span className="admin-subtitle">Gestão de Dados Políticos</span>
          </div>
        </div>
        <div className="admin-header-right">
          <span className="welcome-text">Welcome, {user.full_name}</span>
          <span className="user-role admin">ADMIN</span>
          <Button 
            onClick={handleLogout} 
            className="logout-button"
            icon={<LogoutOutlined />}
          >
            Logout
          </Button>
        </div>
      </header>

      <main className="admin-content">
        {/* Overview Stats */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card className="stat-card">
              <div className="stat-content">
                <UserOutlined className="stat-icon user" />
                <div className="stat-info">
                  <h3>Total Users</h3>
                  <p className="stat-number">1,234</p>
                  <span className="stat-change positive">+12% this month</span>
                </div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card className="stat-card">
              <div className="stat-content">
                <BarChartOutlined className="stat-icon analytics" />
                <div className="stat-info">
                  <h3>Active Influencers</h3>
                  <p className="stat-number">856</p>
                  <span className="stat-change positive">+8% this week</span>
                </div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card className="stat-card">
              <div className="stat-content">
                <DatabaseOutlined className="stat-icon database" />
                <div className="stat-info">
                  <h3>Data Collected</h3>
                  <p className="stat-number">2.4M</p>
                  <span className="stat-change positive">+15% today</span>
                </div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card className="stat-card">
              <div className="stat-content">
                <SettingOutlined className="stat-icon settings" />
                <div className="stat-info">
                  <h3>System Health</h3>
                  <p className="stat-number">98.5%</p>
                  <span className="stat-change positive">All systems operational</span>
                </div>
              </div>
            </Card>
          </Col>
        </Row>

        {/* Management Tabs */}
        <Card className="management-tabs">
          <Tabs 
            defaultActiveKey="users" 
            size="large"
            items={[
              {
                key: 'users',
                label: (
                  <span>
                    <UserOutlined />
                    User Management
                  </span>
                ),
                children: (
                  <>
                    <div className="tab-header">
                      <h3>Manage Users</h3>
                      <Button 
                        type="primary" 
                        icon={<PlusOutlined />}
                        onClick={handleAddUser}
                      >
                        Add New User
                      </Button>
                    </div>
                    <Table 
                      columns={userColumns} 
                      dataSource={mockUsers} 
                      rowKey="id"
                      pagination={{ pageSize: 10 }}
                    />
                  </>
                )
              },
              {
                key: 'influencers',
                label: (
                  <span>
                    <BarChartOutlined />
                    Influencer Management
                  </span>
                ),
                children: (
                  <>
                    <div className="tab-header">
                      <h3>Manage Influencers</h3>
                      <Button 
                        type="primary" 
                        icon={<PlusOutlined />}
                        onClick={handleAddInfluencer}
                      >
                        Add New Influencer
                      </Button>
                    </div>
                    <Table 
                      columns={influencerColumns} 
                      dataSource={mockInfluencers} 
                      rowKey="id"
                      pagination={{ pageSize: 10 }}
                    />
                  </>
                )
              },
              {
                key: 'settings',
                label: (
                  <span>
                    <SettingOutlined />
                    System Settings
                  </span>
                ),
                children: (
                  <div className="settings-content">
                    <h3>System Configuration</h3>
                    <Row gutter={[16, 16]}>
                      <Col span={12}>
                        <Card title="Data Collection Settings" size="small">
                          <p>Configure automatic data collection intervals and sources.</p>
                          <Button>Configure Collection</Button>
                        </Card>
                      </Col>
                      <Col span={12}>
                        <Card title="API Rate Limits" size="small">
                          <p>Manage API rate limits and proxy configurations.</p>
                          <Button>Manage Limits</Button>
                        </Card>
                      </Col>
                      <Col span={12}>
                        <Card title="Notification Settings" size="small">
                          <p>Configure email notifications and alerts.</p>
                          <Button>Setup Notifications</Button>
                        </Card>
                      </Col>
                      <Col span={12}>
                        <Card title="Database Maintenance" size="small">
                          <p>Database backup, optimization, and cleanup tools.</p>
                          <Button>Database Tools</Button>
                        </Card>
                      </Col>
                    </Row>
                  </div>
                )
              }
            ]}
          />
        </Card>
      </main>

      {/* Add User Modal */}
      <Modal
        title="Add New User"
        open={isUserModalVisible}
        onCancel={() => setIsUserModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="Password" rules={[{ required: true, min: 6 }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="firstName" label="First Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="lastName" label="Last Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="role" label="Role" rules={[{ required: true }]}>
            <Select>
              <Option value="guest">Guest</Option>
              <Option value="analyst">Analyst</Option>
              <Option value="admin">Admin</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" style={{ marginRight: 8 }}>
              Create User
            </Button>
            <Button onClick={() => setIsUserModalVisible(false)}>
              Cancel
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* Add Influencer Modal */}
      <Modal
        title="Add New Influencer"
        open={isInfluencerModalVisible}
        onCancel={() => setIsInfluencerModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="username" label="Username" rules={[{ required: true }]}>
            <Input placeholder="@username" />
          </Form.Item>
          <Form.Item name="platform" label="Platform" rules={[{ required: true }]}>
            <Select>
              <Option value="Instagram">Instagram</Option>
              <Option value="YouTube">YouTube</Option>
              <Option value="TikTok">TikTok</Option>
              <Option value="Twitter">Twitter</Option>
            </Select>
          </Form.Item>
          <Form.Item name="followers" label="Follower Count">
            <Input type="number" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" style={{ marginRight: 8 }}>
              Add Influencer
            </Button>
            <Button onClick={() => setIsInfluencerModalVisible(false)}>
              Cancel
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AdminDashboard;