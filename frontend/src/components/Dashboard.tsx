import React, { useState, useEffect } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { Card, Row, Col, Button, Modal, Select, Spin, notification } from 'antd';
import { 
  PlusOutlined, 
  SettingOutlined, 
  DragOutlined,
  TrophyOutlined,
  LineChartOutlined,
  BarChartOutlined,
  PieChartOutlined,
  FireOutlined,
  HeartOutlined
} from '@ant-design/icons';
import { useDrag, useDrop } from 'react-dnd';

import InfluenceLeaderboardWidget from './widgets/InfluenceLeaderboardWidget';
import SentimentOverviewWidget from './widgets/SentimentOverviewWidget';
import TrendingTopicsWidget from './widgets/TrendingTopicsWidget';
import AnalyticsStatsWidget from './widgets/AnalyticsStatsWidget';
import EngagementTrendsWidget from './widgets/EngagementTrendsWidget';
import CollectionStatsWidget from './widgets/CollectionStatsWidget';

import { analyticsService } from '../services/analyticsService';
import { collectionService } from '../services/collectionService';

const { Option } = Select;

interface Widget {
  id: string;
  type: string;
  title: string;
  position: { x: number; y: number; width: number; height: number };
  config: any;
}

interface DashboardData {
  summary: any;
  trending_topics: any[];
  top_performers: any[];
  sentiment_trends: any[];
}

const WIDGET_TYPES = [
  { 
    type: 'influence-leaderboard', 
    title: 'Influence Leaderboard', 
    icon: <TrophyOutlined />,
    description: 'Top influencers by influence score'
  },
  { 
    type: 'sentiment-overview', 
    title: 'Sentiment Overview', 
    icon: <HeartOutlined />,
    description: 'Sentiment analysis distribution'
  },
  { 
    type: 'trending-topics', 
    title: 'Trending Topics', 
    icon: <FireOutlined />,
    description: 'Currently trending hashtags and topics'
  },
  { 
    type: 'analytics-stats', 
    title: 'Analytics Statistics', 
    icon: <BarChartOutlined />,
    description: 'General analytics statistics'
  },
  { 
    type: 'engagement-trends', 
    title: 'Engagement Trends', 
    icon: <LineChartOutlined />,
    description: 'Engagement rate trends over time'
  },
  { 
    type: 'collection-stats', 
    title: 'Collection Status', 
    icon: <PieChartOutlined />,
    description: 'Data collection statistics'
  }
];

const DraggableWidget: React.FC<{
  widget: Widget;
  onMove: (id: string, position: any) => void;
  onRemove: (id: string) => void;
  children: React.ReactNode;
}> = ({ widget, onMove, onRemove, children }) => {
  const [{ isDragging }, drag] = useDrag({
    type: 'widget',
    item: { id: widget.id, type: widget.type },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  return (
    <div
      ref={drag}
      style={{
        opacity: isDragging ? 0.5 : 1,
        cursor: 'move',
        position: 'relative',
        height: '100%'
      }}
    >
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <DragOutlined />
            {widget.title}
          </div>
        }
        extra={
          <Button 
            type="text" 
            size="small"
            onClick={() => onRemove(widget.id)}
          >
            ✕
          </Button>
        }
        style={{ height: '100%' }}
        bodyStyle={{ padding: '12px' }}
      >
        {children}
      </Card>
    </div>
  );
};

const DropZone: React.FC<{
  onDrop: (item: any, monitor: any) => void;
  children: React.ReactNode;
}> = ({ onDrop, children }) => {
  const [{ canDrop, isOver }, drop] = useDrop({
    accept: 'widget',
    drop: onDrop,
    collect: (monitor) => ({
      isOver: monitor.isOver(),
      canDrop: monitor.canDrop(),
    }),
  });

  return (
    <div
      ref={drop}
      style={{
        minHeight: '600px',
        backgroundColor: isOver ? '#f0f0f0' : 'transparent',
        border: canDrop ? '2px dashed #1890ff' : '2px dashed transparent',
        borderRadius: '8px',
        padding: '16px'
      }}
    >
      {children}
    </div>
  );
};

const Dashboard: React.FC = () => {
  const [widgets, setWidgets] = useState<Widget[]>([]);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [addWidgetModalVisible, setAddWidgetModalVisible] = useState(false);
  const [selectedWidgetType, setSelectedWidgetType] = useState<string>('');

  useEffect(() => {
    loadDashboardData();
    loadWidgetLayout();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const data = await analyticsService.getDashboard();
      setDashboardData(data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      notification.error({
        message: 'Error',
        description: 'Failed to load dashboard data'
      });
    } finally {
      setLoading(false);
    }
  };

  const loadWidgetLayout = () => {
    const savedLayout = localStorage.getItem('dashboard_layout');
    if (savedLayout) {
      try {
        setWidgets(JSON.parse(savedLayout));
      } catch (error) {
        console.error('Error loading widget layout:', error);
        // Set default layout
        setDefaultWidgets();
      }
    } else {
      setDefaultWidgets();
    }
  };

  const setDefaultWidgets = () => {
    const defaultWidgets: Widget[] = [
      {
        id: 'analytics-stats-1',
        type: 'analytics-stats',
        title: 'Analytics Overview',
        position: { x: 0, y: 0, width: 12, height: 200 },
        config: {}
      },
      {
        id: 'influence-leaderboard-1',
        type: 'influence-leaderboard',
        title: 'Top Influencers',
        position: { x: 0, y: 1, width: 8, height: 400 },
        config: { limit: 10 }
      },
      {
        id: 'sentiment-overview-1',
        type: 'sentiment-overview',
        title: 'Sentiment Analysis',
        position: { x: 8, y: 1, width: 4, height: 400 },
        config: { days_back: 7 }
      },
      {
        id: 'trending-topics-1',
        type: 'trending-topics',
        title: 'Trending Now',
        position: { x: 0, y: 2, width: 6, height: 350 },
        config: { limit: 8 }
      },
      {
        id: 'collection-stats-1',
        type: 'collection-stats',
        title: 'Collection Status',
        position: { x: 6, y: 2, width: 6, height: 350 },
        config: {}
      }
    ];
    
    setWidgets(defaultWidgets);
  };

  const saveWidgetLayout = (newWidgets: Widget[]) => {
    localStorage.setItem('dashboard_layout', JSON.stringify(newWidgets));
    setWidgets(newWidgets);
  };

  const addWidget = () => {
    if (!selectedWidgetType) return;

    const widgetType = WIDGET_TYPES.find(type => type.type === selectedWidgetType);
    if (!widgetType) return;

    const newWidget: Widget = {
      id: `${selectedWidgetType}-${Date.now()}`,
      type: selectedWidgetType,
      title: widgetType.title,
      position: { x: 0, y: widgets.length, width: 6, height: 300 },
      config: {}
    };

    const updatedWidgets = [...widgets, newWidget];
    saveWidgetLayout(updatedWidgets);
    setAddWidgetModalVisible(false);
    setSelectedWidgetType('');
  };

  const removeWidget = (widgetId: string) => {
    const updatedWidgets = widgets.filter(w => w.id !== widgetId);
    saveWidgetLayout(updatedWidgets);
  };

  const moveWidget = (widgetId: string, newPosition: any) => {
    const updatedWidgets = widgets.map(w =>
      w.id === widgetId ? { ...w, position: { ...w.position, ...newPosition } } : w
    );
    saveWidgetLayout(updatedWidgets);
  };

  const handleDrop = (item: any, monitor: any) => {
    // Handle widget reordering/repositioning
    const dropResult = monitor.getDropResult();
    if (item && dropResult) {
      // Calculate new position based on drop location
      const newPosition = {
        x: Math.floor(Math.random() * 8), // Simplified positioning
        y: Math.floor(Math.random() * 10)
      };
      moveWidget(item.id, newPosition);
    }
  };

  const renderWidget = (widget: Widget) => {
    if (!dashboardData) return null;

    const commonProps = {
      data: dashboardData,
      config: widget.config
    };

    switch (widget.type) {
      case 'influence-leaderboard':
        return <InfluenceLeaderboardWidget {...commonProps} />;
      case 'sentiment-overview':
        return <SentimentOverviewWidget {...commonProps} />;
      case 'trending-topics':
        return <TrendingTopicsWidget {...commonProps} />;
      case 'analytics-stats':
        return <AnalyticsStatsWidget {...commonProps} />;
      case 'engagement-trends':
        return <EngagementTrendsWidget {...commonProps} />;
      case 'collection-stats':
        return <CollectionStatsWidget {...commonProps} />;
      default:
        return <div>Unknown widget type: {widget.type}</div>;
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <DndProvider backend={HTML5Backend}>
      <div style={{ padding: '24px' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          marginBottom: '24px' 
        }}>
          <h1>Analytics Dashboard</h1>
          <div>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setAddWidgetModalVisible(true)}
              style={{ marginRight: '8px' }}
            >
              Add Widget
            </Button>
            <Button
              icon={<SettingOutlined />}
              onClick={() => setDefaultWidgets()}
            >
              Reset Layout
            </Button>
          </div>
        </div>

        <DropZone onDrop={handleDrop}>
          <Row gutter={[16, 16]}>
            {widgets.map(widget => (
              <Col
                key={widget.id}
                xs={24}
                sm={12}
                md={widget.position.width || 6}
                lg={widget.position.width || 6}
                xl={widget.position.width || 6}
              >
                <div style={{ height: widget.position.height || 300 }}>
                  <DraggableWidget
                    widget={widget}
                    onMove={moveWidget}
                    onRemove={removeWidget}
                  >
                    {renderWidget(widget)}
                  </DraggableWidget>
                </div>
              </Col>
            ))}
          </Row>
        </DropZone>

        {widgets.length === 0 && (
          <div style={{ 
            textAlign: 'center', 
            padding: '50px',
            border: '2px dashed #d9d9d9',
            borderRadius: '8px'
          }}>
            <PlusOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
            <h3>No widgets added</h3>
            <p>Click "Add Widget" to start customizing your dashboard</p>
            <Button 
              type="primary" 
              onClick={() => setAddWidgetModalVisible(true)}
            >
              Add Your First Widget
            </Button>
          </div>
        )}

        <Modal
          title="Add Widget"
          visible={addWidgetModalVisible}
          onOk={addWidget}
          onCancel={() => {
            setAddWidgetModalVisible(false);
            setSelectedWidgetType('');
          }}
          okButtonProps={{ disabled: !selectedWidgetType }}
        >
          <div style={{ marginBottom: '16px' }}>
            <label>Select widget type:</label>
            <Select
              style={{ width: '100%', marginTop: '8px' }}
              placeholder="Choose a widget type"
              value={selectedWidgetType}
              onChange={setSelectedWidgetType}
            >
              {WIDGET_TYPES.map(type => (
                <Option key={type.type} value={type.type}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {type.icon}
                    <div>
                      <div style={{ fontWeight: 'bold' }}>{type.title}</div>
                      <div style={{ fontSize: '12px', color: '#666' }}>
                        {type.description}
                      </div>
                    </div>
                  </div>
                </Option>
              ))}
            </Select>
          </div>
        </Modal>
      </div>
    </DndProvider>
  );
};

export default Dashboard;