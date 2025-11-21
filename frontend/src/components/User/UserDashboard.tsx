import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Card, Row, Col, Progress, Timeline } from 'antd';
import {
  BarChartOutlined,
  PieChartOutlined,
  TrophyOutlined,
  HeartOutlined,
  UserOutlined,
  FireOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import DashboardNavigation from '../Navigation/DashboardNavigation';
import './UserDashboard.css';

const UserDashboard: React.FC = () => {
  const { user } = useAuth();

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <DashboardNavigation>
      <div className="user-dashboard">
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
                <div className="leaderboard-item">
                  <span className="rank">6</span>
                  <div className="influencer-info">
                    <span className="influencer-name">@music_producer</span>
                    <span className="platform">TikTok</span>
                  </div>
                  <span className="score">84.1</span>
                </div>
                <div className="leaderboard-item">
                  <span className="rank">7</span>
                  <div className="influencer-info">
                    <span className="influencer-name">@gaming_streamer</span>
                    <span className="platform">Twitch</span>
                  </div>
                  <span className="score">82.7</span>
                </div>
                <div className="leaderboard-item">
                  <span className="rank">8</span>
                  <div className="influencer-info">
                    <span className="influencer-name">@fashion_stylist</span>
                    <span className="platform">Instagram</span>
                  </div>
                  <span className="score">81.3</span>
                </div>
                <div className="leaderboard-item">
                  <span className="rank">9</span>
                  <div className="influencer-info">
                    <span className="influencer-name">@book_reviewer</span>
                    <span className="platform">YouTube</span>
                  </div>
                  <span className="score">79.8</span>
                </div>
                <div className="leaderboard-item">
                  <span className="rank">10</span>
                  <div className="influencer-info">
                    <span className="influencer-name">@crypto_analyst</span>
                    <span className="platform">Twitter</span>
                  </div>
                  <span className="score">78.4</span>
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
                <div className="trending-item">
                  <span className="trend-topic">#FoodTech</span>
                  <span className="trend-growth positive">↗ +7%</span>
                </div>
                <div className="trending-item">
                  <span className="trend-topic">#RemoteWork</span>
                  <span className="trend-growth negative">↘ -2%</span>
                </div>
                <div className="trending-item">
                  <span className="trend-topic">#Cryptocurrency</span>
                  <span className="trend-growth positive">↗ +14%</span>
                </div>
                <div className="trending-item">
                  <span className="trend-topic">#ClimateChange</span>
                  <span className="trend-growth positive">↗ +6%</span>
                </div>
                <div className="trending-item">
                  <span className="trend-topic">#EdTech</span>
                  <span className="trend-growth positive">↗ +9%</span>
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
              <Timeline
                items={[
                  {
                    color: 'green',
                    children: (
                      <div className="activity-item">
                        <span className="activity-text">@techguru123 - New analytics processed</span>
                        <span className="activity-time">2 minutes ago</span>
                      </div>
                    )
                  },
                  {
                    color: 'blue',
                    children: (
                      <div className="activity-item">
                        <span className="activity-text">@lifestyle_blogger - Sentiment analysis complete</span>
                        <span className="activity-time">5 minutes ago</span>
                      </div>
                    )
                  },
                  {
                    color: 'orange',
                    children: (
                      <div className="activity-item">
                        <span className="activity-text">@fitness_influencer - Data collection started</span>
                        <span className="activity-time">1 hour ago</span>
                      </div>
                    )
                  },
                  {
                    color: 'gray',
                    children: (
                      <div className="activity-item">
                        <span className="activity-text">System: Weekly analytics report generated</span>
                        <span className="activity-time">3 hours ago</span>
                      </div>
                    )
                  },
                  {
                    color: 'purple',
                    children: (
                      <div className="activity-item">
                        <span className="activity-text">@music_producer - New content engagement spike detected</span>
                        <span className="activity-time">4 hours ago</span>
                      </div>
                    )
                  },
                  {
                    color: 'green',
                    children: (
                      <div className="activity-item">
                        <span className="activity-text">@gaming_streamer - Viral post detected</span>
                        <span className="activity-time">6 hours ago</span>
                      </div>
                    )
                  },
                  {
                    color: 'blue',
                    children: (
                      <div className="activity-item">
                        <span className="activity-text">@fashion_stylist - Brand partnership analysis complete</span>
                        <span className="activity-time">8 hours ago</span>
                      </div>
                    )
                  },
                  {
                    color: 'orange',
                    children: (
                      <div className="activity-item">
                        <span className="activity-text">@book_reviewer - Monthly performance report ready</span>
                        <span className="activity-time">10 hours ago</span>
                      </div>
                    )
                  },
                  {
                    color: 'red',
                    children: (
                      <div className="activity-item">
                        <span className="activity-text">@crypto_analyst - Market sentiment shift detected</span>
                        <span className="activity-time">12 hours ago</span>
                      </div>
                    )
                  }
                ]}
              />
            </Card>
          </Col>
        </Row>
        </main>
      </div>
    </DashboardNavigation>
  );
};

export default UserDashboard;