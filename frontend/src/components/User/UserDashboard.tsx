import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Card, Row, Col, Button, Progress, Timeline } from 'antd';
import {
  BarChartOutlined,
  PieChartOutlined,
  TrophyOutlined,
  HeartOutlined,
  LogoutOutlined,
  UserOutlined,
  FireOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import PolitikosLogo, { PolitikosLogoText } from '../Brand/PolitikosLogo';
import './UserDashboard.css';

const UserDashboard: React.FC = () => {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <div className="user-dashboard">
      <header className="user-header">
        <div className="user-header-left">
          <PolitikosLogoText size="large" className="user-logo" />
          <div className="user-title">
            <h1>Análises Políticas</h1>
            <span className="user-subtitle">Dashboard de Dados e Tendências</span>
          </div>
        </div>
        <div className="user-header-right">
          <span className="welcome-text">Welcome, {user.full_name}</span>
          <span className="user-role">{user.role.toUpperCase()}</span>
          <Button 
            onClick={handleLogout} 
            className="logout-button"
            icon={<LogoutOutlined />}
          >
            Logout
          </Button>
        </div>
      </header>

      <main className="user-content">
        {/* User Profile Overview */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={8}>
            <Card className="profile-card">
              <div className="profile-content">
                <UserOutlined className="profile-icon" />
                <div className="profile-info">
                  <h3>{user.full_name}</h3>
                  <p className="profile-email">{user.email}</p>
                  <span className="profile-role">{user.role}</span>
                </div>
              </div>
              <div className="profile-status">
                <div className="status-item">
                  <span className="status-label">Account Status:</span>
                  <span className="status-value active">
                    {user.is_active ? '✅ Active' : '❌ Inactive'}
                  </span>
                </div>
                <div className="status-item">
                  <span className="status-label">Email Verified:</span>
                  <span className="status-value">
                    {user.email_verified ? '✅ Verified' : '❌ Unverified'}
                  </span>
                </div>
              </div>
            </Card>
          </Col>
          <Col span={16}>
            <Card className="access-card">
              <h3>Your Access Level: {user.role.toUpperCase()}</h3>
              <div className="access-features">
                <div className="feature-item available">
                  <BarChartOutlined className="feature-icon" />
                  <span>View Analytics Reports</span>
                  <span className="feature-status">✅ Available</span>
                </div>
                <div className="feature-item available">
                  <PieChartOutlined className="feature-icon" />
                  <span>Sentiment Analysis</span>
                  <span className="feature-status">✅ Available</span>
                </div>
                <div className="feature-item available">
                  <TrophyOutlined className="feature-icon" />
                  <span>Influence Rankings</span>
                  <span className="feature-status">✅ Available</span>
                </div>
                <div className={`feature-item ${user.role === 'admin' || user.role === 'analyst' ? 'available' : 'restricted'}`}>
                  <FireOutlined className="feature-icon" />
                  <span>Advanced Analytics</span>
                  <span className="feature-status">
                    {user.role === 'admin' || user.role === 'analyst' ? '✅ Available' : '🔒 Restricted'}
                  </span>
                </div>
              </div>
            </Card>
          </Col>
        </Row>

        {/* Analytics Overview Cards */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card className="metric-card">
              <div className="metric-content">
                <div className="metric-header">
                  <BarChartOutlined className="metric-icon analytics" />
                  <span className="metric-title">Tracked Influencers</span>
                </div>
                <div className="metric-value">1,234</div>
                <div className="metric-change positive">+12% from last month</div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card className="metric-card">
              <div className="metric-content">
                <div className="metric-header">
                  <HeartOutlined className="metric-icon engagement" />
                  <span className="metric-title">Avg Engagement</span>
                </div>
                <div className="metric-value">8.5%</div>
                <div className="metric-change positive">+2.3% this week</div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card className="metric-card">
              <div className="metric-content">
                <div className="metric-header">
                  <TrophyOutlined className="metric-icon influence" />
                  <span className="metric-title">Top Influence Score</span>
                </div>
                <div className="metric-value">94.2</div>
                <div className="metric-change positive">+5.1 points</div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card className="metric-card">
              <div className="metric-content">
                <div className="metric-header">
                  <ThunderboltOutlined className="metric-icon activity" />
                  <span className="metric-title">Active Posts</span>
                </div>
                <div className="metric-value">24.7K</div>
                <div className="metric-change positive">+18% today</div>
              </div>
            </Card>
          </Col>
        </Row>

        {/* Main Content Panels */}
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Card 
              title={
                <span>
                  <PieChartOutlined style={{ marginRight: 8 }} />
                  Sentiment Analysis Overview
                </span>
              }
              className="analysis-card"
            >
              <div className="sentiment-stats">
                <div className="sentiment-item positive">
                  <div className="sentiment-circle positive">😊</div>
                  <div className="sentiment-info">
                    <span className="sentiment-label">Positive</span>
                    <span className="sentiment-percentage">68%</span>
                  </div>
                  <Progress 
                    percent={68} 
                    strokeColor="#52c41a" 
                    showInfo={false} 
                    size="small"
                  />
                </div>
                <div className="sentiment-item neutral">
                  <div className="sentiment-circle neutral">😐</div>
                  <div className="sentiment-info">
                    <span className="sentiment-label">Neutral</span>
                    <span className="sentiment-percentage">22%</span>
                  </div>
                  <Progress 
                    percent={22} 
                    strokeColor="#faad14" 
                    showInfo={false} 
                    size="small"
                  />
                </div>
                <div className="sentiment-item negative">
                  <div className="sentiment-circle negative">😞</div>
                  <div className="sentiment-info">
                    <span className="sentiment-label">Negative</span>
                    <span className="sentiment-percentage">10%</span>
                  </div>
                  <Progress 
                    percent={10} 
                    strokeColor="#ff4d4f" 
                    showInfo={false} 
                    size="small"
                  />
                </div>
              </div>
            </Card>
          </Col>
          <Col span={12}>
            <Card 
              title={
                <span>
                  <TrophyOutlined style={{ marginRight: 8 }} />
                  Top Performing Influencers
                </span>
              }
              className="leaderboard-card"
            >
              <div className="leaderboard">
                <div className="leaderboard-item">
                  <span className="rank gold">1</span>
                  <div className="influencer-info">
                    <span className="influencer-name">@techguru123</span>
                    <span className="platform">Instagram</span>
                  </div>
                  <span className="score">94.2</span>
                </div>
                <div className="leaderboard-item">
                  <span className="rank silver">2</span>
                  <div className="influencer-info">
                    <span className="influencer-name">@lifestyle_blogger</span>
                    <span className="platform">YouTube</span>
                  </div>
                  <span className="score">91.8</span>
                </div>
                <div className="leaderboard-item">
                  <span className="rank bronze">3</span>
                  <div className="influencer-info">
                    <span className="influencer-name">@fitness_influencer</span>
                    <span className="platform">TikTok</span>
                  </div>
                  <span className="score">89.5</span>
                </div>
                <div className="leaderboard-item">
                  <span className="rank">4</span>
                  <div className="influencer-info">
                    <span className="influencer-name">@food_explorer</span>
                    <span className="platform">Instagram</span>
                  </div>
                  <span className="score">87.2</span>
                </div>
                <div className="leaderboard-item">
                  <span className="rank">5</span>
                  <div className="influencer-info">
                    <span className="influencer-name">@travel_adventures</span>
                    <span className="platform">YouTube</span>
                  </div>
                  <span className="score">85.9</span>
                </div>
              </div>
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={12}>
            <Card 
              title={
                <span>
                  <FireOutlined style={{ marginRight: 8 }} />
                  Trending Topics
                </span>
              }
              className="trending-card"
            >
              <div className="trending-list">
                <div className="trending-item">
                  <span className="trend-topic">#TechInnovation</span>
                  <span className="trend-growth positive">↗ +15%</span>
                </div>
                <div className="trending-item">
                  <span className="trend-topic">#SustainableLiving</span>
                  <span className="trend-growth positive">↗ +8%</span>
                </div>
                <div className="trending-item">
                  <span className="trend-topic">#DigitalMarketing</span>
                  <span className="trend-growth negative">↘ -3%</span>
                </div>
                <div className="trending-item">
                  <span className="trend-topic">#AITrends</span>
                  <span className="trend-growth positive">↗ +22%</span>
                </div>
                <div className="trending-item">
                  <span className="trend-topic">#HealthWellness</span>
                  <span className="trend-growth positive">↗ +11%</span>
                </div>
              </div>
            </Card>
          </Col>
          <Col span={12}>
            <Card 
              title={
                <span>
                  <HeartOutlined style={{ marginRight: 8 }} />
                  Recent Activity
                </span>
              }
              className="activity-card"
            >
              <Timeline>
                <Timeline.Item color="green">
                  <div className="activity-item">
                    <span className="activity-text">@techguru123 - New analytics processed</span>
                    <span className="activity-time">2 minutes ago</span>
                  </div>
                </Timeline.Item>
                <Timeline.Item color="blue">
                  <div className="activity-item">
                    <span className="activity-text">@lifestyle_blogger - Sentiment analysis complete</span>
                    <span className="activity-time">5 minutes ago</span>
                  </div>
                </Timeline.Item>
                <Timeline.Item color="orange">
                  <div className="activity-item">
                    <span className="activity-text">@fitness_influencer - Data collection started</span>
                    <span className="activity-time">1 hour ago</span>
                  </div>
                </Timeline.Item>
                <Timeline.Item color="gray">
                  <div className="activity-item">
                    <span className="activity-text">System: Weekly analytics report generated</span>
                    <span className="activity-time">3 hours ago</span>
                  </div>
                </Timeline.Item>
              </Timeline>
            </Card>
          </Col>
        </Row>
      </main>
    </div>
  );
};

export default UserDashboard;