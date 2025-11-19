import React from 'react';
import { Row, Col, Statistic, Card } from 'antd';
import { 
  UserOutlined, 
  FileTextOutlined, 
  MessageOutlined, 
  TrophyOutlined,
  RiseOutlined,
  TeamOutlined,
  BarChartOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';

interface AnalyticsStatsWidgetProps {
  data: {
    summary: {
      total_influencers: number;
      active_influencers: number;
      total_posts_analyzed: number;
      total_comments_analyzed: number;
      trending_topics_count: number;
      influencers_with_analytics: number;
      avg_influence_score: number;
      platforms: {
        [key: string]: number;
      };
    };
  };
  config: {};
}

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  } else if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num?.toLocaleString() || '0';
};

const AnalyticsStatsWidget: React.FC<AnalyticsStatsWidgetProps> = ({ data }) => {
  const { summary } = data;

  if (!summary) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <BarChartOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
        <p style={{ color: '#999', marginTop: '16px' }}>
          No analytics data available
        </p>
      </div>
    );
  }

  const stats = [
    {
      title: 'Total Influencers',
      value: summary.total_influencers || 0,
      prefix: <UserOutlined style={{ color: '#1890ff' }} />,
      color: '#1890ff'
    },
    {
      title: 'Active Influencers',
      value: summary.active_influencers || 0,
      prefix: <TeamOutlined style={{ color: '#52c41a' }} />,
      color: '#52c41a'
    },
    {
      title: 'Posts Analyzed',
      value: summary.total_posts_analyzed || 0,
      prefix: <FileTextOutlined style={{ color: '#722ed1' }} />,
      color: '#722ed1',
      formatted: true
    },
    {
      title: 'Comments Analyzed',
      value: summary.total_comments_analyzed || 0,
      prefix: <MessageOutlined style={{ color: '#fa8c16' }} />,
      color: '#fa8c16',
      formatted: true
    },
    {
      title: 'Trending Topics',
      value: summary.trending_topics_count || 0,
      prefix: <ThunderboltOutlined style={{ color: '#eb2f96' }} />,
      color: '#eb2f96'
    },
    {
      title: 'With Analytics',
      value: summary.influencers_with_analytics || 0,
      prefix: <RiseOutlined style={{ color: '#13c2c2' }} />,
      color: '#13c2c2'
    },
    {
      title: 'Avg Influence Score',
      value: summary.avg_influence_score || 0,
      prefix: <TrophyOutlined style={{ color: '#faad14' }} />,
      color: '#faad14',
      precision: 1,
      suffix: '/100'
    }
  ];

  // Platform distribution
  const platformStats = summary.platforms ? Object.entries(summary.platforms).map(([platform, count]) => ({
    platform: platform.charAt(0).toUpperCase() + platform.slice(1),
    count: count as number,
    percentage: summary.total_influencers > 0 ? (count as number / summary.total_influencers * 100).toFixed(1) : '0'
  })) : [];

  return (
    <div style={{ height: '100%' }}>
      {/* Main Statistics */}
      <Row gutter={[8, 8]} style={{ marginBottom: '16px' }}>
        {stats.slice(0, 4).map((stat, index) => (
          <Col span={6} key={index}>
            <Card 
              size="small" 
              style={{ 
                textAlign: 'center',
                border: `1px solid ${stat.color}20`,
                backgroundColor: `${stat.color}05`
              }}
            >
              <Statistic
                title={
                  <div style={{ 
                    fontSize: '11px', 
                    color: '#666',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}>
                    {stat.title}
                  </div>
                }
                value={stat.formatted ? formatNumber(stat.value) : stat.value}
                valueStyle={{ 
                  color: stat.color, 
                  fontSize: '16px',
                  fontWeight: 'bold'
                }}
                prefix={stat.prefix}
                precision={stat.precision}
                suffix={stat.suffix}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {/* Secondary Statistics */}
      <Row gutter={[8, 8]} style={{ marginBottom: '16px' }}>
        {stats.slice(4).map((stat, index) => (
          <Col span={8} key={index}>
            <Card 
              size="small" 
              style={{ 
                textAlign: 'center',
                border: `1px solid ${stat.color}20`,
                backgroundColor: `${stat.color}05`
              }}
            >
              <Statistic
                title={
                  <div style={{ 
                    fontSize: '11px', 
                    color: '#666',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}>
                    {stat.title}
                  </div>
                }
                value={stat.value}
                valueStyle={{ 
                  color: stat.color, 
                  fontSize: '14px',
                  fontWeight: 'bold'
                }}
                prefix={stat.prefix}
                precision={stat.precision}
                suffix={stat.suffix}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {/* Platform Distribution */}
      {platformStats.length > 0 && (
        <Card 
          title="Platform Distribution" 
          size="small"
          style={{ marginTop: '8px' }}
          bodyStyle={{ padding: '12px' }}
        >
          <Row gutter={[8, 4]}>
            {platformStats.map((platform, index) => (
              <Col span={12} key={index}>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '12px',
                  padding: '2px 0'
                }}>
                  <span style={{ color: '#666' }}>
                    {platform.platform}
                  </span>
                  <span style={{ fontWeight: 'bold' }}>
                    {platform.count} ({platform.percentage}%)
                  </span>
                </div>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* Quick Insights */}
      <div style={{ 
        marginTop: '12px', 
        padding: '8px', 
        backgroundColor: '#f9f9f9', 
        borderRadius: '4px',
        fontSize: '11px',
        color: '#666'
      }}>
        <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
          Quick Insights:
        </div>
        <div>
          • {((summary.active_influencers / summary.total_influencers) * 100 || 0).toFixed(0)}% of influencers are actively tracked
        </div>
        <div>
          • {((summary.total_posts_analyzed / summary.total_influencers) || 0).toFixed(1)} posts analyzed per influencer
        </div>
        {summary.avg_influence_score && (
          <div>
            • Average influence score: {summary.avg_influence_score.toFixed(1)}/100
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalyticsStatsWidget;