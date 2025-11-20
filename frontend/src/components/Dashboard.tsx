import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Button, Spin } from 'antd';
import { 
  PlusOutlined, 
  BarChartOutlined,
  PieChartOutlined,
  FireOutlined,
  HeartOutlined
} from '@ant-design/icons';

// Simple static widgets for now
const SimpleWidget: React.FC<{ title: string; content: string; color: string }> = ({ title, content, color }) => (
  <Card 
    title={title}
    style={{ 
      marginBottom: 16,
      borderTop: `4px solid ${color}`
    }}
    size="small"
  >
    <div style={{ textAlign: 'center', padding: '20px 0' }}>
      <div style={{ fontSize: '24px', fontWeight: 'bold', color }}>{content}</div>
      <div style={{ color: '#666', marginTop: 8 }}>Sample Data</div>
    </div>
  </Card>
);

interface Widget {
  id: string;
  type: string;
  title: string;
  content: string;
  color: string;
  span: number;
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [widgets] = useState<Widget[]>([
    {
      id: '1',
      type: 'stats',
      title: 'Total Influencers',
      content: '1,234',
      color: '#1890ff',
      span: 6
    },
    {
      id: '2',
      type: 'stats',
      title: 'Active Collections',
      content: '56',
      color: '#52c41a',
      span: 6
    },
    {
      id: '3',
      type: 'stats',
      title: 'Analytics Processed',
      content: '98.5%',
      color: '#722ed1',
      span: 6
    },
    {
      id: '4',
      type: 'stats',
      title: 'Sentiment Score',
      content: '8.2/10',
      color: '#eb2f96',
      span: 6
    }
  ]);

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '60vh' 
      }}>
        <Spin size="large" tip="Loading Dashboard..." />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 24 
      }}>
        <h2 style={{ margin: 0 }}>
          <BarChartOutlined style={{ marginRight: 8 }} />
          Analytics Dashboard
        </h2>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => console.log('Add widget clicked')}
        >
          Add Widget
        </Button>
      </div>

      <Row gutter={[16, 16]}>
        {widgets.map((widget) => (
          <Col key={widget.id} span={widget.span}>
            <SimpleWidget 
              title={widget.title}
              content={widget.content}
              color={widget.color}
            />
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card 
            title={
              <span>
                <PieChartOutlined style={{ marginRight: 8 }} />
                Sentiment Overview
              </span>
            }
            size="small"
          >
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <div style={{ fontSize: '18px', color: '#52c41a' }}>😊 Positive: 68%</div>
              <div style={{ fontSize: '18px', color: '#faad14', margin: '8px 0' }}>😐 Neutral: 22%</div>
              <div style={{ fontSize: '18px', color: '#ff4d4f' }}>😞 Negative: 10%</div>
            </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card 
            title={
              <span>
                <FireOutlined style={{ marginRight: 8 }} />
                Trending Topics
              </span>
            }
            size="small"
          >
            <div style={{ padding: '20px 0' }}>
              <div style={{ marginBottom: 12 }}>
                <span style={{ fontWeight: 'bold' }}>#TechInnovation</span>
                <span style={{ float: 'right', color: '#52c41a' }}>↗ +15%</span>
              </div>
              <div style={{ marginBottom: 12 }}>
                <span style={{ fontWeight: 'bold' }}>#SustainableLiving</span>
                <span style={{ float: 'right', color: '#52c41a' }}>↗ +8%</span>
              </div>
              <div style={{ marginBottom: 12 }}>
                <span style={{ fontWeight: 'bold' }}>#DigitalMarketing</span>
                <span style={{ float: 'right', color: '#ff4d4f' }}>↘ -3%</span>
              </div>
              <div>
                <span style={{ fontWeight: 'bold' }}>#AITrends</span>
                <span style={{ float: 'right', color: '#52c41a' }}>↗ +22%</span>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      <Card 
        title={
          <span>
            <HeartOutlined style={{ marginRight: 8 }} />
            Recent Activity
          </span>
        }
        style={{ marginTop: 16 }}
        size="small"
      >
        <div style={{ padding: '20px 0' }}>
          <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between' }}>
            <span>@techguru123 - New analytics processed</span>
            <span style={{ color: '#666' }}>2 minutes ago</span>
          </div>
          <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between' }}>
            <span>@lifestyle_blogger - Sentiment analysis complete</span>
            <span style={{ color: '#666' }}>5 minutes ago</span>
          </div>
          <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between' }}>
            <span>@fitness_influencer - Data collection started</span>
            <span style={{ color: '#666' }}>1 hour ago</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>System: Weekly analytics report generated</span>
            <span style={{ color: '#666' }}>3 hours ago</span>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Dashboard;