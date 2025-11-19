import React from 'react';
import { List, Avatar, Tag, Progress } from 'antd';
import { TrophyOutlined, UserOutlined } from '@ant-design/icons';

interface InfluenceLeaderboardWidgetProps {
  data: {
    top_performers: Array<{
      influencer: {
        id: number;
        username: string;
        display_name: string;
        platform: string;
        verified: boolean;
        follower_count: number;
        profile_image_url?: string;
      };
      analytics: {
        influence_score: number;
        engagement_rate: number;
      };
    }>;
  };
  config: {
    limit?: number;
  };
}

const PLATFORM_COLORS = {
  instagram: '#E4405F',
  youtube: '#FF0000',
  tiktok: '#000000',
  twitter: '#1DA1F2'
};

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  } else if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
};

const InfluenceLeaderboardWidget: React.FC<InfluenceLeaderboardWidgetProps> = ({ 
  data, 
  config 
}) => {
  const { top_performers = [] } = data;
  const { limit = 10 } = config;

  const topPerformers = top_performers.slice(0, limit);

  if (topPerformers.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <TrophyOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
        <p style={{ color: '#999', marginTop: '16px' }}>
          No influencer data available
        </p>
      </div>
    );
  }

  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <List
        dataSource={topPerformers}
        renderItem={(item, index) => (
          <List.Item
            style={{
              padding: '12px',
              borderBottom: '1px solid #f0f0f0',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              width: '100%',
              gap: '12px'
            }}>
              <div style={{
                minWidth: '24px',
                height: '24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'bold',
                color: index < 3 ? '#faad14' : '#666'
              }}>
                {index + 1}
              </div>

              <Avatar
                src={item.influencer.profile_image_url}
                icon={<UserOutlined />}
                size={40}
              />

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px',
                  marginBottom: '4px'
                }}>
                  <span style={{ 
                    fontWeight: 'bold',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {item.influencer.display_name || item.influencer.username}
                  </span>
                  
                  {item.influencer.verified && (
                    <Tag color="blue" size="small">✓</Tag>
                  )}
                  
                  <Tag 
                    color={PLATFORM_COLORS[item.influencer.platform as keyof typeof PLATFORM_COLORS]}
                    size="small"
                  >
                    {item.influencer.platform.toUpperCase()}
                  </Tag>
                </div>

                <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                  @{item.influencer.username} • {formatNumber(item.influencer.follower_count)} followers
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ 
                      fontSize: '11px', 
                      color: '#999', 
                      marginBottom: '2px' 
                    }}>
                      Influence Score
                    </div>
                    <Progress
                      percent={item.analytics.influence_score}
                      size="small"
                      showInfo={false}
                      strokeColor={{
                        '0%': '#108ee9',
                        '100%': '#87d068',
                      }}
                    />
                  </div>
                  
                  <div style={{ 
                    fontSize: '14px', 
                    fontWeight: 'bold',
                    color: '#1890ff'
                  }}>
                    {item.analytics.influence_score.toFixed(1)}
                  </div>
                </div>

                <div style={{ 
                  fontSize: '11px', 
                  color: '#999', 
                  marginTop: '4px' 
                }}>
                  {item.analytics.engagement_rate.toFixed(2)}% engagement
                </div>
              </div>
            </div>
          </List.Item>
        )}
      />
      
      {topPerformers.length === 0 && (
        <div style={{ 
          textAlign: 'center', 
          color: '#999', 
          padding: '20px' 
        }}>
          No influencer rankings available
        </div>
      )}
    </div>
  );
};

export default InfluenceLeaderboardWidget;