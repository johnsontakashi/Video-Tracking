import React from 'react';
import { Line } from '@ant-design/plots';
import { Empty } from 'antd';
import { LineChartOutlined } from '@ant-design/icons';

interface EngagementTrendsWidgetProps {
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

const EngagementTrendsWidget: React.FC<EngagementTrendsWidgetProps> = ({ 
  data, 
  config 
}) => {
  const { sentiment_trends = [] } = data;

  // Transform data for line chart
  const chartData = sentiment_trends.flatMap(trend => {
    const date = new Date(trend.date).toLocaleDateString();
    const total = Object.values(trend.counts).reduce((a, b) => a + b, 0);
    
    return [
      {
        date,
        type: 'Positive',
        value: trend.counts.positive,
        percentage: total > 0 ? (trend.counts.positive / total * 100) : 0
      },
      {
        date,
        type: 'Neutral',
        value: trend.counts.neutral,
        percentage: total > 0 ? (trend.counts.neutral / total * 100) : 0
      },
      {
        date,
        type: 'Negative',
        value: trend.counts.negative,
        percentage: total > 0 ? (trend.counts.negative / total * 100) : 0
      },
      {
        date,
        type: 'Mixed',
        value: trend.counts.mixed,
        percentage: total > 0 ? (trend.counts.mixed / total * 100) : 0
      }
    ];
  });

  const config_chart = {
    data: chartData,
    xField: 'date',
    yField: 'percentage',
    seriesField: 'type',
    smooth: true,
    color: ['#52c41a', '#faad14', '#f5222d', '#722ed1'],
    legend: {
      position: 'top' as const,
    },
    tooltip: {
      formatter: (datum: any) => {
        return {
          name: datum.type,
          value: `${datum.percentage.toFixed(1)}% (${datum.value} posts)`
        };
      },
    },
    xAxis: {
      label: {
        style: {
          fontSize: 10,
        },
      },
    },
    yAxis: {
      label: {
        style: {
          fontSize: 10,
        },
        formatter: (v: string) => `${v}%`,
      },
    },
    interactions: [{ type: 'marker-active' }],
    point: {
      size: 3,
      shape: 'circle',
    },
  };

  if (sentiment_trends.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <LineChartOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
        <p style={{ color: '#999', marginTop: '16px' }}>
          No engagement trend data available
        </p>
      </div>
    );
  }

  return (
    <div style={{ height: '100%', padding: '8px' }}>
      <div style={{ 
        fontSize: '12px', 
        color: '#666', 
        marginBottom: '8px',
        textAlign: 'center'
      }}>
        Sentiment Distribution Over Time (%)
      </div>
      
      <div style={{ height: 'calc(100% - 30px)' }}>
        <Line {...config_chart} />
      </div>
    </div>
  );
};

export default EngagementTrendsWidget;