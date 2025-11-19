import React from 'react';
import { Row, Col, Statistic, Card, Progress, Tag } from 'antd';
import { 
  ClockCircleOutlined, 
  CheckCircleOutlined, 
  ExclamationCircleOutlined,
  SyncOutlined,
  PauseCircleOutlined,
  WarningOutlined
} from '@ant-design/icons';

interface CollectionStatsWidgetProps {
  data: {
    summary: any; // We'll add collection stats to dashboard data
  };
  config: {};
}

// Mock collection stats - in real implementation, this would come from the API
const mockCollectionStats = {
  total_tasks: 1250,
  pending_tasks: 45,
  running_tasks: 8,
  completed_tasks: 1180,
  failed_tasks: 17,
  success_rate: 94.8,
  avg_collection_time: 2.3, // minutes
  platforms: {
    instagram: { active: 12, total: 350 },
    youtube: { active: 3, total: 120 },
    tiktok: { active: 5, total: 200 },
    twitter: { active: 2, total: 80 }
  },
  recent_activity: [
    { platform: 'instagram', action: 'posts', count: 150, time: '2 min ago' },
    { platform: 'youtube', action: 'profile', count: 1, time: '5 min ago' },
    { platform: 'tiktok', action: 'comments', count: 89, time: '8 min ago' }
  ]
};

const PLATFORM_COLORS = {
  instagram: '#E4405F',
  youtube: '#FF0000',
  tiktok: '#000000',
  twitter: '#1DA1F2'
};

const STATUS_ICONS = {
  pending: { icon: <ClockCircleOutlined />, color: '#faad14' },
  running: { icon: <SyncOutlined spin />, color: '#1890ff' },
  completed: { icon: <CheckCircleOutlined />, color: '#52c41a' },
  failed: { icon: <ExclamationCircleOutlined />, color: '#f5222d' },
  paused: { icon: <PauseCircleOutlined />, color: '#d9d9d9' }
};

const formatNumber = (num: number): string => {
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toLocaleString();
};

const CollectionStatsWidget: React.FC<CollectionStatsWidgetProps> = ({ data, config }) => {
  const stats = mockCollectionStats; // In real app: data.collection_stats

  const taskStats = [
    {
      title: 'Completed',
      value: stats.completed_tasks,
      ...STATUS_ICONS.completed
    },
    {
      title: 'Running',
      value: stats.running_tasks,
      ...STATUS_ICONS.running
    },
    {
      title: 'Pending',
      value: stats.pending_tasks,
      ...STATUS_ICONS.pending
    },
    {
      title: 'Failed',
      value: stats.failed_tasks,
      ...STATUS_ICONS.failed
    }
  ];

  const totalActiveTasks = Object.values(stats.platforms).reduce(
    (sum, platform) => sum + platform.active, 0
  );

  return (
    <div style={{ height: '100%' }}>
      {/* Success Rate & Performance */}
      <Row gutter={[8, 8]} style={{ marginBottom: '12px' }}>
        <Col span={12}>
          <Card size="small" style={{ textAlign: 'center' }}>
            <Statistic
              title="Success Rate"
              value={stats.success_rate}
              precision={1}
              suffix="%"
              valueStyle={{ 
                color: stats.success_rate >= 90 ? '#52c41a' : '#faad14',
                fontSize: '18px'
              }}
            />
            <Progress
              percent={stats.success_rate}
              showInfo={false}
              strokeColor={stats.success_rate >= 90 ? '#52c41a' : '#faad14'}
              size="small"
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card size="small" style={{ textAlign: 'center' }}>
            <Statistic
              title="Avg Time"
              value={stats.avg_collection_time}
              precision={1}
              suffix="min"
              valueStyle={{ fontSize: '18px', color: '#1890ff' }}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Task Status Distribution */}
      <Row gutter={[4, 4]} style={{ marginBottom: '12px' }}>
        {taskStats.map((stat, index) => (
          <Col span={6} key={index}>
            <Card 
              size="small" 
              style={{ 
                textAlign: 'center',
                border: `1px solid ${stat.color}30`,
                backgroundColor: `${stat.color}08`
              }}
            >
              <div style={{ color: stat.color, fontSize: '16px', marginBottom: '4px' }}>
                {stat.icon}
              </div>
              <div style={{ 
                fontSize: '14px', 
                fontWeight: 'bold',
                color: stat.color 
              }}>
                {formatNumber(stat.value)}
              </div>
              <div style={{ 
                fontSize: '10px', 
                color: '#666',
                whiteSpace: 'nowrap'
              }}>
                {stat.title}
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Platform Activity */}
      <Card 
        title="Platform Activity" 
        size="small"
        style={{ marginBottom: '12px' }}
        bodyStyle={{ padding: '8px' }}
      >
        <Row gutter={[4, 4]}>
          {Object.entries(stats.platforms).map(([platform, data], index) => (
            <Col span={12} key={index}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '4px 8px',
                backgroundColor: '#f9f9f9',
                borderRadius: '4px',
                border: `2px solid ${PLATFORM_COLORS[platform as keyof typeof PLATFORM_COLORS]}20`
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <div 
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: PLATFORM_COLORS[platform as keyof typeof PLATFORM_COLORS]
                    }}
                  />
                  <span style={{ fontSize: '11px', textTransform: 'capitalize' }}>
                    {platform}
                  </span>
                </div>
                <div style={{ fontSize: '11px', fontWeight: 'bold' }}>
                  {data.active}/{data.total}
                </div>
              </div>
            </Col>
          ))}
        </Row>
        
        <div style={{ 
          textAlign: 'center', 
          marginTop: '8px',
          fontSize: '11px',
          color: '#666'
        }}>
          {totalActiveTasks} active collections
        </div>
      </Card>

      {/* Recent Activity */}
      <Card 
        title="Recent Activity" 
        size="small"
        bodyStyle={{ padding: '8px' }}
      >
        <div style={{ maxHeight: '80px', overflow: 'auto' }}>
          {stats.recent_activity.map((activity, index) => (
            <div 
              key={index}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '4px 0',
                borderBottom: index < stats.recent_activity.length - 1 ? '1px solid #f0f0f0' : 'none',
                fontSize: '11px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Tag 
                  color={PLATFORM_COLORS[activity.platform as keyof typeof PLATFORM_COLORS]}
                  size="small"
                  style={{ margin: 0, fontSize: '10px' }}
                >
                  {activity.platform}
                </Tag>
                <span>{activity.action}: {activity.count}</span>
              </div>
              <span style={{ color: '#999' }}>{activity.time}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Status Indicator */}
      <div style={{
        position: 'absolute',
        top: '8px',
        right: '8px',
        display: 'flex',
        alignItems: 'center',
        gap: '4px'
      }}>
        <div style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: stats.running_tasks > 0 ? '#52c41a' : '#faad14',
          animation: stats.running_tasks > 0 ? 'pulse 2s infinite' : 'none'
        }} />
        <span style={{ fontSize: '10px', color: '#666' }}>
          {stats.running_tasks > 0 ? 'Active' : 'Idle'}
        </span>
      </div>

      <style>
        {`
          @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
          }
        `}
      </style>
    </div>
  );
};

export default CollectionStatsWidget;