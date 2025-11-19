import React from 'react';
import { List, Tag, Progress, Typography } from 'antd';
import { FireOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface TrendingTopicsWidgetProps {
  data: {
    trending_topics: Array<{
      id: number;
      topic: string;
      hashtag: string;
      mention_count: number;
      velocity: number;
      growth_rate: number;
      sentiment: {
        positive: number;
        neutral: number;
        negative: number;
      };
      category: string;
      trending_since: string;
    }>;
  };
  config: {
    limit?: number;
  };
}

const formatTimeAgo = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
  
  if (diffInHours < 1) {
    return 'Just now';
  } else if (diffInHours < 24) {
    return `${Math.floor(diffInHours)}h ago`;
  } else {
    return `${Math.floor(diffInHours / 24)}d ago`;
  }
};

const getSentimentColor = (sentiment: { positive: number; neutral: number; negative: number }) => {
  const total = sentiment.positive + sentiment.neutral + sentiment.negative;
  if (total === 0) return '#faad14';
  
  const positiveRatio = sentiment.positive / total;
  const negativeRatio = sentiment.negative / total;
  
  if (positiveRatio > 0.6) return '#52c41a';
  if (negativeRatio > 0.6) return '#f5222d';
  return '#faad14';
};

const getCategoryColor = (category: string) => {
  const colors: { [key: string]: string } = {
    'technology': '#1890ff',
    'fashion': '#eb2f96',
    'sports': '#52c41a',
    'entertainment': '#722ed1',
    'food': '#fa8c16',
    'travel': '#13c2c2',
    'general': '#666666'
  };
  
  return colors[category.toLowerCase()] || colors.general;
};

const TrendingTopicsWidget: React.FC<TrendingTopicsWidgetProps> = ({ 
  data, 
  config 
}) => {
  const { trending_topics = [] } = data;
  const { limit = 10 } = config;

  const displayTopics = trending_topics
    .sort((a, b) => b.velocity - a.velocity)
    .slice(0, limit);

  if (displayTopics.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <FireOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
        <p style={{ color: '#999', marginTop: '16px' }}>
          No trending topics found
        </p>
      </div>
    );
  }

  const maxVelocity = Math.max(...displayTopics.map(t => t.velocity));

  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <List
        dataSource={displayTopics}
        renderItem={(item, index) => (
          <List.Item
            style={{
              padding: '12px 8px',
              borderBottom: '1px solid #f0f0f0'
            }}
          >
            <div style={{ width: '100%' }}>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'flex-start',
                marginBottom: '8px'
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '8px',
                    marginBottom: '4px'
                  }}>
                    <span style={{ 
                      fontWeight: 'bold',
                      color: index < 3 ? '#fa541c' : '#262626',
                      fontSize: index < 3 ? '16px' : '14px'
                    }}>
                      {item.hashtag || item.topic}
                    </span>
                    
                    {index < 3 && <FireOutlined style={{ color: '#fa541c' }} />}
                    
                    <Tag 
                      color={getCategoryColor(item.category)}
                      size="small"
                    >
                      {item.category}
                    </Tag>
                  </div>

                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '12px',
                    fontSize: '12px',
                    color: '#666'
                  }}>
                    <span>{item.mention_count.toLocaleString()} mentions</span>
                    <span>•</span>
                    <span>{formatTimeAgo(item.trending_since)}</span>
                    {item.growth_rate !== 0 && (
                      <>
                        <span>•</span>
                        <span style={{ 
                          color: item.growth_rate > 0 ? '#52c41a' : '#f5222d',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '2px'
                        }}>
                          {item.growth_rate > 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                          {Math.abs(item.growth_rate).toFixed(1)}%
                        </span>
                      </>
                    )}
                  </div>
                </div>

                <div style={{ textAlign: 'right', minWidth: '60px' }}>
                  <Text style={{ 
                    fontSize: '14px', 
                    fontWeight: 'bold',
                    color: '#1890ff'
                  }}>
                    {item.velocity.toFixed(1)}/h
                  </Text>
                </div>
              </div>

              <div style={{ marginBottom: '6px' }}>
                <Progress
                  percent={(item.velocity / maxVelocity) * 100}
                  showInfo={false}
                  size="small"
                  strokeColor={index < 3 ? '#fa541c' : '#1890ff'}
                  trailColor="#f0f0f0"
                />
              </div>

              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div style={{ fontSize: '11px', color: '#999' }}>
                  Velocity: {item.velocity.toFixed(1)} mentions/hour
                </div>
                
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: getSentimentColor(item.sentiment),
                  title: 'Sentiment indicator'
                }} />
              </div>
            </div>
          </List.Item>
        )}
      />
    </div>
  );
};

export default TrendingTopicsWidget;