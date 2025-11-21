import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Progress,
  Tag,
  Select,
  DatePicker,
  Space,
  Button,
  Spin
} from 'antd';
import {
  TrophyOutlined,
  UserOutlined,
  LikeOutlined,
  EyeOutlined,
  RiseOutlined,
  DownloadOutlined,
  FilterOutlined
} from '@ant-design/icons';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { useAuth } from '../../contexts/AuthContext';
import './AnalyticsDashboard.css';

const { Option } = Select;
const { RangePicker } = DatePicker;

interface AnalyticsData {
  total_influencers: number;
  total_posts: number;
  total_engagement: number;
  avg_engagement_rate: number;
  top_platforms: Array<{ platform: string; count: number }>;
  engagement_trend: Array<{ date: string; engagement: number }>;
}

interface TopInfluencer {
  username: string;
  platform: string;
  followers: number;
  engagement_rate: number;
  posts_this_month: number;
}

const COLORS = ['#00cc6c', '#ffd93d', '#0000cc', '#ff6b6b', '#4ecdc4', '#45b7d1'];

const platformColors = {
  instagram: '#E4405F',
  youtube: '#FF0000',
  twitter: '#1DA1F2',
  tiktok: '#000000'
};

const getMockAnalyticsData = (): AnalyticsData => ({
  total_influencers: 1247,
  total_posts: 8456,
  total_engagement: 342567,
  avg_engagement_rate: 4.2,
  top_platforms: [
    { platform: 'Instagram', count: 520 },
    { platform: 'YouTube', count: 340 },
    { platform: 'TikTok', count: 287 },
    { platform: 'Twitter', count: 100 }
  ],
  engagement_trend: [
    { date: '2024-01-01', engagement: 12450 },
    { date: '2024-01-02', engagement: 13200 },
    { date: '2024-01-03', engagement: 11800 },
    { date: '2024-01-04', engagement: 14600 },
    { date: '2024-01-05', engagement: 15100 },
    { date: '2024-01-06', engagement: 13900 },
    { date: '2024-01-07', engagement: 16200 }
  ]
});

const AnalyticsDashboard: React.FC = () => {
  const { user } = useAuth();
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d');

  // Mock data for top influencers
  const topInfluencers: TopInfluencer[] = [
    {
      username: 'techguru123',
      platform: 'instagram',
      followers: 125000,
      engagement_rate: 4.2,
      posts_this_month: 15
    },
    {
      username: 'fashionista_rio',
      platform: 'instagram',
      followers: 89000,
      engagement_rate: 3.8,
      posts_this_month: 12
    },
    {
      username: 'fitness_coach_sp',
      platform: 'youtube',
      followers: 67000,
      engagement_rate: 5.1,
      posts_this_month: 8
    }
  ];

  // Mock sentiment data
  const sentimentData = [
    { name: 'Positive', value: 65, color: '#52c41a' },
    { name: 'Neutral', value: 25, color: '#faad14' },
    { name: 'Negative', value: 10, color: '#f5222d' }
  ];

  // Mock engagement by hour data
  const engagementByHour = [
    { hour: '00:00', engagement: 120 },
    { hour: '06:00', engagement: 180 },
    { hour: '12:00', engagement: 450 },
    { hour: '18:00', engagement: 780 },
    { hour: '22:00', engagement: 340 }
  ];

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      
      // Check if we should use mock data
      const useMockData = process.env.REACT_APP_USE_MOCK_DATA === 'true' || 
                         process.env.NODE_ENV === 'development';
      
      if (useMockData) {
        console.log('Using mock analytics data');
        // Simulate loading time
        await new Promise(resolve => setTimeout(resolve, 500));
        setAnalyticsData(getMockAnalyticsData());
        return;
      }
      
      // Try to fetch from backend
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/analytics/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      
      if (data.summary) {
        setAnalyticsData({
          total_influencers: data.summary.total_influencers || 0,
          total_posts: data.summary.total_posts || 0,
          total_engagement: data.summary.total_engagement || 0,
          avg_engagement_rate: data.summary.avg_engagement_rate || 0,
          top_platforms: data.summary.top_platforms || [],
          engagement_trend: data.summary.engagement_trend || []
        });
      } else {
        setAnalyticsData(getMockAnalyticsData());
      }
    } catch (error) {
      console.warn('Failed to fetch analytics from backend, using mock data');
      setAnalyticsData(getMockAnalyticsData());
    } finally {
      setLoading(false);
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

  const influencerColumns = [
    {
      title: 'Influencer',
      dataIndex: 'username',
      key: 'username',
      render: (username: string, record: TopInfluencer) => (
        <div>
          <div style={{ fontWeight: 500 }}>@{username}</div>
          <Tag color={platformColors[record.platform as keyof typeof platformColors]}>
            {record.platform}
          </Tag>
        </div>
      )
    },
    {
      title: 'Followers',
      dataIndex: 'followers',
      key: 'followers',
      render: (followers: number) => formatNumber(followers),
      sorter: (a: TopInfluencer, b: TopInfluencer) => a.followers - b.followers
    },
    {
      title: 'Engagement Rate',
      dataIndex: 'engagement_rate',
      key: 'engagement_rate',
      render: (rate: number) => (
        <div>
          <Progress
            percent={rate * 20} // Scale 0-5% to 0-100%
            showInfo={false}
            strokeColor={rate > 4 ? '#52c41a' : rate > 2 ? '#faad14' : '#f5222d'}
            size="small"
          />
          <span style={{ fontSize: '12px', marginLeft: 8 }}>{rate}%</span>
        </div>
      ),
      sorter: (a: TopInfluencer, b: TopInfluencer) => a.engagement_rate - b.engagement_rate
    },
    {
      title: 'Posts This Month',
      dataIndex: 'posts_this_month',
      key: 'posts_this_month',
      sorter: (a: TopInfluencer, b: TopInfluencer) => a.posts_this_month - b.posts_this_month
    }
  ];

  if (loading || !analyticsData) {
    return (
      <div className="analytics-dashboard">
        <div className="loading-container">
          <Spin size="large" />
          <div style={{ marginTop: 16, color: '#666' }}>Loading analytics...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="analytics-dashboard">
      <div className="dashboard-header">
        <h2>Analytics Overview</h2>
        <Space>
          <Select
            value={timeRange}
            onChange={setTimeRange}
            style={{ width: 120 }}
          >
            <Option value="7d">Last 7 days</Option>
            <Option value="30d">Last 30 days</Option>
            <Option value="90d">Last 90 days</Option>
          </Select>
          <Button icon={<DownloadOutlined />}>
            Export Report
          </Button>
        </Space>
      </div>

      {/* Key Metrics */}
      <Row gutter={[16, 16]} className="metrics-row">
        <Col xs={24} sm={12} lg={6}>
          <Card className="metric-card">
            <Statistic
              title="Total Influencers"
              value={analyticsData.total_influencers}
              prefix={<UserOutlined style={{ color: '#00cc6c' }} />}
              valueStyle={{ color: '#00cc6c' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="metric-card">
            <Statistic
              title="Total Posts"
              value={analyticsData.total_posts}
              prefix={<EyeOutlined style={{ color: '#ffd93d' }} />}
              valueStyle={{ color: '#ffd93d' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="metric-card">
            <Statistic
              title="Total Engagement"
              value={analyticsData.total_engagement}
              prefix={<LikeOutlined style={{ color: '#0000cc' }} />}
              valueStyle={{ color: '#0000cc' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="metric-card">
            <Statistic
              title="Avg Engagement Rate"
              value={analyticsData.avg_engagement_rate}
              suffix="%"
              prefix={<RiseOutlined style={{ color: '#ff6b6b' }} />}
              valueStyle={{ color: '#ff6b6b' }}
              precision={1}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts Section */}
      <Row gutter={[16, 16]} className="charts-row">
        <Col xs={24} lg={16}>
          <Card title="Engagement Trend" className="chart-card">
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={analyticsData.engagement_trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="engagement"
                  stroke="#00cc6c"
                  fill="#00cc6c"
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Platform Distribution" className="chart-card">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analyticsData.top_platforms}
                  dataKey="count"
                  nameKey="platform"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={(entry: any) => entry.platform}
                >
                  {analyticsData.top_platforms.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="charts-row">
        <Col xs={24} lg={12}>
          <Card title="Sentiment Analysis" className="chart-card">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={sentimentData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  label={(entry) => `${entry.name}: ${entry.value}%`}
                >
                  {sentimentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Engagement by Hour" className="chart-card">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={engagementByHour}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="engagement" fill="#00cc6c" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Top Influencers Table */}
      <Row>
        <Col span={24}>
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <TrophyOutlined style={{ color: '#ffd93d' }} />
                Top Performing Influencers
              </div>
            }
            className="influencers-table-card"
          >
            <Table
              columns={influencerColumns}
              dataSource={topInfluencers}
              rowKey="username"
              pagination={false}
              size="middle"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AnalyticsDashboard;