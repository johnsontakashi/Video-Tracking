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
  Tooltip,
  Badge
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  UserOutlined,
  InstagramOutlined,
  YoutubeOutlined,
  TwitterOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import './InfluencerList.css';

const { Option } = Select;
const { Search } = Input;

interface Influencer {
  id: number;
  external_id: string;
  username: string;
  display_name?: string;
  platform: string;
  bio?: string;
  profile_image_url?: string;
  verified: boolean;
  follower_count: number;
  following_count: number;
  post_count: number;
  engagement_rate: number;
  status: string;
  created_at: string;
  owner_name?: string;
}

const platformIcons = {
  instagram: <InstagramOutlined style={{ color: '#E4405F' }} />,
  youtube: <YoutubeOutlined style={{ color: '#FF0000' }} />,
  twitter: <TwitterOutlined style={{ color: '#1DA1F2' }} />,
  tiktok: <span style={{ color: '#000000' }}>🎵</span>
};

const platformColors = {
  instagram: '#E4405F',
  youtube: '#FF0000',
  twitter: '#1DA1F2',
  tiktok: '#000000'
};

const InfluencerList: React.FC = () => {
  const { user } = useAuth();
  const [influencers, setInfluencers] = useState<Influencer[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingInfluencer, setEditingInfluencer] = useState<Influencer | null>(null);
  const [searchText, setSearchText] = useState('');
  const [platformFilter, setPlatformFilter] = useState<string>('');
  const [form] = Form.useForm();

  useEffect(() => {
    fetchInfluencers();
  }, []);

  const fetchInfluencers = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      
      const response = await fetch('/api/influencers', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      
      if (data.success) {
        setInfluencers(data.influencers);
      } else {
        message.error('Failed to load influencers');
      }
    } catch (error) {
      console.error('Error fetching influencers:', error);
      message.error('Failed to load influencers');
    } finally {
      setLoading(false);
    }
  };

  const handleAddInfluencer = () => {
    setEditingInfluencer(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEditInfluencer = (influencer: Influencer) => {
    setEditingInfluencer(influencer);
    form.setFieldsValue(influencer);
    setIsModalVisible(true);
  };

  const handleSubmit = async (values: any) => {
    try {
      const token = localStorage.getItem('access_token');
      const method = editingInfluencer ? 'PUT' : 'POST';
      const url = editingInfluencer 
        ? `/api/influencers/${editingInfluencer.id}`
        : '/api/influencers';

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
          editingInfluencer 
            ? 'Influencer updated successfully' 
            : 'Influencer added successfully'
        );
        setIsModalVisible(false);
        fetchInfluencers();
      } else {
        message.error(data.message || 'Operation failed');
      }
    } catch (error) {
      console.error('Error saving influencer:', error);
      message.error('Failed to save influencer');
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const filteredInfluencers = influencers.filter(influencer => {
    const matchesSearch = !searchText || 
      influencer.username.toLowerCase().includes(searchText.toLowerCase()) ||
      (influencer.display_name && influencer.display_name.toLowerCase().includes(searchText.toLowerCase()));
    
    const matchesPlatform = !platformFilter || influencer.platform === platformFilter;
    
    return matchesSearch && matchesPlatform;
  });

  const columns = [
    {
      title: 'Influencer',
      key: 'influencer',
      render: (record: Influencer) => (
        <div className="influencer-info">
          <Avatar
            size={40}
            src={record.profile_image_url}
            icon={<UserOutlined />}
            className="influencer-avatar"
          />
          <div className="influencer-details">
            <div className="influencer-name">
              <span className="display-name">
                {record.display_name || record.username}
              </span>
              {record.verified && (
                <CheckCircleOutlined 
                  style={{ color: '#1890ff', marginLeft: 4 }} 
                  title="Verified Account"
                />
              )}
            </div>
            <div className="influencer-username">@{record.username}</div>
          </div>
        </div>
      )
    },
    {
      title: 'Platform',
      dataIndex: 'platform',
      key: 'platform',
      render: (platform: string) => (
        <Tag 
          color={platformColors[platform as keyof typeof platformColors]}
          icon={platformIcons[platform as keyof typeof platformIcons]}
        >
          {platform.charAt(0).toUpperCase() + platform.slice(1)}
        </Tag>
      ),
      filters: [
        { text: 'Instagram', value: 'instagram' },
        { text: 'YouTube', value: 'youtube' },
        { text: 'Twitter', value: 'twitter' },
        { text: 'TikTok', value: 'tiktok' }
      ],
      onFilter: (value: any, record: Influencer) => record.platform === value
    },
    {
      title: 'Followers',
      dataIndex: 'follower_count',
      key: 'followers',
      render: (count: number) => formatNumber(count),
      sorter: (a: Influencer, b: Influencer) => a.follower_count - b.follower_count
    },
    {
      title: 'Posts',
      dataIndex: 'post_count',
      key: 'posts',
      render: (count: number) => formatNumber(count),
      sorter: (a: Influencer, b: Influencer) => a.post_count - b.post_count
    },
    {
      title: 'Engagement Rate',
      dataIndex: 'engagement_rate',
      key: 'engagement',
      render: (rate: number) => (
        <Badge
          count={`${rate}%`}
          style={{ 
            backgroundColor: rate > 5 ? '#52c41a' : rate > 2 ? '#faad14' : '#f5222d' 
          }}
        />
      ),
      sorter: (a: Influencer, b: Influencer) => a.engagement_rate - b.engagement_rate
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'orange'}>
          {status.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: Influencer) => (
        <Space>
          <Tooltip title="Edit">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEditInfluencer(record)}
            />
          </Tooltip>
          <Tooltip title="Delete">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => {
                Modal.confirm({
                  title: 'Delete Influencer',
                  content: `Are you sure you want to delete @${record.username}?`,
                  okText: 'Delete',
                  okType: 'danger',
                  onOk: () => {
                    // TODO: Implement delete
                    message.info('Delete functionality coming soon');
                  }
                });
              }}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <div className="influencer-list">
      <Card
        title={
          <div className="page-header">
            <h2>Influencer Management</h2>
            <span className="subtitle">Manage and track your influencers</span>
          </div>
        }
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAddInfluencer}
          >
            Add Influencer
          </Button>
        }
      >
        <div className="filters-section">
          <Space size="middle" wrap>
            <Search
              placeholder="Search influencers..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 300 }}
              prefix={<SearchOutlined />}
            />
            <Select
              placeholder="Filter by platform"
              style={{ width: 150 }}
              value={platformFilter}
              onChange={setPlatformFilter}
              allowClear
            >
              <Option value="instagram">Instagram</Option>
              <Option value="youtube">YouTube</Option>
              <Option value="twitter">Twitter</Option>
              <Option value="tiktok">TikTok</Option>
            </Select>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={filteredInfluencers}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `Total ${total} influencers`
          }}
          scroll={{ x: 800 }}
        />
      </Card>

      <Modal
        title={editingInfluencer ? 'Edit Influencer' : 'Add New Influencer'}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          className="influencer-form"
        >
          <Form.Item
            label="Username"
            name="username"
            rules={[{ required: true, message: 'Username is required' }]}
          >
            <Input placeholder="Enter username (without @)" />
          </Form.Item>

          <Form.Item
            label="Display Name"
            name="display_name"
          >
            <Input placeholder="Enter display name" />
          </Form.Item>

          <Form.Item
            label="Platform"
            name="platform"
            rules={[{ required: true, message: 'Platform is required' }]}
          >
            <Select placeholder="Select platform">
              <Option value="instagram">
                {platformIcons.instagram} Instagram
              </Option>
              <Option value="youtube">
                {platformIcons.youtube} YouTube
              </Option>
              <Option value="twitter">
                {platformIcons.twitter} Twitter
              </Option>
              <Option value="tiktok">
                {platformIcons.tiktok} TikTok
              </Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="Bio"
            name="bio"
          >
            <Input.TextArea
              rows={3}
              placeholder="Enter bio/description"
            />
          </Form.Item>

          <div className="form-row">
            <Form.Item
              label="Followers"
              name="follower_count"
              style={{ width: '48%' }}
            >
              <Input
                type="number"
                placeholder="0"
                min={0}
              />
            </Form.Item>

            <Form.Item
              label="Following"
              name="following_count"
              style={{ width: '48%' }}
            >
              <Input
                type="number"
                placeholder="0"
                min={0}
              />
            </Form.Item>
          </div>

          <Form.Item
            label="Post Count"
            name="post_count"
          >
            <Input
              type="number"
              placeholder="0"
              min={0}
            />
          </Form.Item>

          <div className="form-actions">
            <Space>
              <Button onClick={() => setIsModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                {editingInfluencer ? 'Update' : 'Add'} Influencer
              </Button>
            </Space>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default InfluencerList;