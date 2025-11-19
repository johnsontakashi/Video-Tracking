import React from 'react';
import { Pie } from '@ant-design/plots';
import { Card, Statistic, Row, Col } from 'antd';
import { 
  SmileOutlined, 
  MehOutlined, 
  FrownOutlined,
  HeartOutlined 
} from '@ant-design/icons';

interface SentimentOverviewWidgetProps {
  data: {
    sentiment_trends: Array<{
      date: string;
      counts: {
        positive: number;
        neutral: number;
        negative: number;
        mixed: number;
      };
    }>;
  };
  config: {
    days_back?: number;
  };
}

const SentimentOverviewWidget: React.FC<SentimentOverviewWidgetProps> = ({ 
  data, 
  config 
}) => {
  const { sentiment_trends = [] } = data;

  // Aggregate sentiment data
  const totalSentiments = sentiment_trends.reduce(
    (acc, trend) => ({
      positive: acc.positive + trend.counts.positive,
      neutral: acc.neutral + trend.counts.neutral,
      negative: acc.negative + trend.counts.negative,
      mixed: acc.mixed + trend.counts.mixed
    }),
    { positive: 0, neutral: 0, negative: 0, mixed: 0 }
  );

  const total = Object.values(totalSentiments).reduce((a, b) => a + b, 0);

  const pieData = [
    {
      type: 'Positive',
      value: totalSentiments.positive,
      percentage: total > 0 ? (totalSentiments.positive / total * 100).toFixed(1) : '0'
    },
    {
      type: 'Neutral', 
      value: totalSentiments.neutral,
      percentage: total > 0 ? (totalSentiments.neutral / total * 100).toFixed(1) : '0'
    },
    {
      type: 'Negative',
      value: totalSentiments.negative,
      percentage: total > 0 ? (totalSentiments.negative / total * 100).toFixed(1) : '0'
    },
    {
      type: 'Mixed',
      value: totalSentiments.mixed,
      percentage: total > 0 ? (totalSentiments.mixed / total * 100).toFixed(1) : '0'
    }
  ].filter(item => item.value > 0);

  const config_chart = {
    data: pieData,
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    innerRadius: 0.5,
    label: {
      type: 'spider',
      labelHeight: 28,
      content: '{name}\n{percentage}%',
      style: {
        fontSize: 12,
      },
    },
    color: ['#52c41a', '#faad14', '#f5222d', '#722ed1'],
    interactions: [{ type: 'element-active' }],
    statistic: {
      title: {
        style: {
          whiteSpace: 'pre-wrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        },
        content: 'Total\nAnalyzed',
      },
      content: {
        style: {
          whiteSpace: 'pre-wrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        },
        content: total.toLocaleString(),
      },
    },
  };

  if (total === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <HeartOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
        <p style={{ color: '#999', marginTop: '16px' }}>
          No sentiment data available
        </p>
      </div>
    );
  }

  return (
    <div style={{ height: '100%' }}>
      <Row gutter={[8, 8]} style={{ marginBottom: '16px' }}>
        <Col span={6}>
          <Card size="small" style={{ textAlign: 'center', border: '1px solid #52c41a' }}>
            <Statistic
              value={totalSentiments.positive}
              valueStyle={{ color: '#52c41a', fontSize: '16px' }}
              prefix={<SmileOutlined />}
              suffix={`${total > 0 ? (totalSentiments.positive / total * 100).toFixed(0) : 0}%`}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" style={{ textAlign: 'center', border: '1px solid #faad14' }}>
            <Statistic
              value={totalSentiments.neutral}
              valueStyle={{ color: '#faad14', fontSize: '16px' }}
              prefix={<MehOutlined />}
              suffix={`${total > 0 ? (totalSentiments.neutral / total * 100).toFixed(0) : 0}%`}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" style={{ textAlign: 'center', border: '1px solid #f5222d' }}>
            <Statistic
              value={totalSentiments.negative}
              valueStyle={{ color: '#f5222d', fontSize: '16px' }}
              prefix={<FrownOutlined />}
              suffix={`${total > 0 ? (totalSentiments.negative / total * 100).toFixed(0) : 0}%`}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" style={{ textAlign: 'center', border: '1px solid #722ed1' }}>
            <Statistic
              value={totalSentiments.mixed}
              valueStyle={{ color: '#722ed1', fontSize: '16px' }}
              prefix="⚡"
              suffix={`${total > 0 ? (totalSentiments.mixed / total * 100).toFixed(0) : 0}%`}
            />
          </Card>
        </Col>
      </Row>

      <div style={{ height: 'calc(100% - 80px)' }}>
        <Pie {...config_chart} />
      </div>
    </div>
  );
};

export default SentimentOverviewWidget;