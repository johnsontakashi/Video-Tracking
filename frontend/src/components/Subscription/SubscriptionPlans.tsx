import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Row,
  Col,
  Tag,
  Badge,
  Switch,
  Divider,
  Modal,
  message,
  Spin,
  Space,
  Typography
} from 'antd';
import {
  CheckOutlined,
  CrownOutlined,
  StarOutlined,
  RocketOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  SafetyCertificateOutlined
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import { paymentService } from '../../services/paymentService';
import './SubscriptionPlans.css';

const { Title, Text } = Typography;

interface Plan {
  id: number;
  plan_type: string;
  name: string;
  price: number;
  influencer_limit: number;
  posts_per_month: number;
  analytics_retention_days: number;
  features: string[];
  is_active: boolean;
}

const planIcons = {
  free: <StarOutlined />,
  starter: <RocketOutlined />,
  professional: <CrownOutlined />,
  enterprise: <TrophyOutlined />
};

const planColors = {
  free: '#52c41a',
  starter: '#1890ff',
  professional: '#722ed1',
  enterprise: '#fa8c16'
};

const featureDescriptions: { [key: string]: string } = {
  basic_analytics: 'Basic performance metrics and insights',
  manual_tracking: 'Manual influencer tracking and monitoring',
  advanced_analytics: 'Advanced analytics with detailed reports',
  automated_tracking: 'Automated data collection and updates',
  sentiment_analysis: 'AI-powered sentiment analysis',
  premium_analytics: 'Premium analytics with custom dashboards',
  real_time_tracking: 'Real-time data updates and monitoring',
  competitor_analysis: 'Competitor tracking and comparison',
  custom_reports: 'Custom report generation and exports',
  enterprise_analytics: 'Enterprise-grade analytics platform',
  api_access: 'Full API access for integrations',
  white_label: 'White-label solution for your brand',
  dedicated_support: '24/7 dedicated customer support'
};

const getMockPlans = (): Plan[] => [
  {
    id: 1,
    plan_type: 'starter',
    name: 'Basic',
    price: 29,
    influencer_limit: 100,
    posts_per_month: 1000,
    analytics_retention_days: 90,
    features: ['basic_analytics', 'manual_tracking'],
    is_active: true
  },
  {
    id: 2,
    plan_type: 'professional',
    name: 'Professional',
    price: 99,
    influencer_limit: 1000,
    posts_per_month: 10000,
    analytics_retention_days: 365,
    features: ['advanced_analytics', 'automated_tracking', 'sentiment_analysis'],
    is_active: true
  },
  {
    id: 3,
    plan_type: 'enterprise',
    name: 'Enterprise',
    price: 299,
    influencer_limit: -1, // unlimited
    posts_per_month: -1, // unlimited
    analytics_retention_days: -1, // unlimited
    features: ['enterprise_analytics', 'api_access', 'white_label', 'dedicated_support'],
    is_active: true
  }
];

const SubscriptionPlans: React.FC = () => {
  const { user } = useAuth();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [isYearly, setIsYearly] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [upgradeModalVisible, setUpgradeModalVisible] = useState(false);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000';
      const response = await fetch(`${apiUrl}/api/payment/plans`, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.plans) {
        setPlans(data.plans);
      } else {
        // If backend doesn't have plans service, use mock data
        setPlans(getMockPlans());
        console.log('Using mock subscription plans data');
      }
    } catch (error) {
      console.error('Error fetching plans:', error);
      // Use mock data as fallback
      setPlans(getMockPlans());
      console.log('Backend unavailable, using mock subscription plans data');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = (plan: Plan) => {
    setSelectedPlan(plan);
    setUpgradeModalVisible(true);
  };

  const confirmUpgrade = async () => {
    if (!selectedPlan) return;

    try {
      // Simulate upgrade process
      message.loading('Processing upgrade...', 2);
      
      setTimeout(() => {
        message.success(`Successfully upgraded to ${selectedPlan.name}!`);
        setUpgradeModalVisible(false);
        setSelectedPlan(null);
      }, 2000);
      
    } catch (error) {
      console.error('Error upgrading plan:', error);
      message.error('Failed to upgrade plan');
    }
  };

  const formatPrice = (price: number) => {
    if (price === 0) return 'Free';
    const yearlyPrice = isYearly ? (price * 10).toFixed(2) : null; // 2 months free
    const displayPrice = isYearly ? yearlyPrice : price.toFixed(2);
    
    return (
      <div className="price-display">
        <span className="currency">$</span>
        <span className="amount">{displayPrice}</span>
        <span className="period">/{isYearly ? 'year' : 'month'}</span>
        {isYearly && price > 0 && (
          <div className="savings">
            <Tag color="green">
              Save ${ (price * 2).toFixed(2) }
            </Tag>
          </div>
        )}
      </div>
    );
  };

  const formatLimit = (limit: number, suffix: string = '') => {
    if (limit === -1) return `Unlimited ${suffix}`;
    return `${limit.toLocaleString()} ${suffix}`;
  };

  const isCurrentPlan = (planType: string) => {
    return user?.current_plan === planType;
  };

  const isRecommended = (planType: string) => {
    return planType === 'professional';
  };

  if (loading) {
    return (
      <div className="subscription-plans">
        <div className="loading-container">
          <Spin size="large" />
          <div style={{ marginTop: 16, color: '#666' }}>Loading subscription plans...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="subscription-plans">
      <div className="plans-header">
        <div className="header-content">
          <Title level={2}>Choose Your Plan</Title>
          <Text className="header-description">
            Scale your influencer analytics with plans designed for every need
          </Text>
        </div>
        
        <div className="billing-toggle">
          <Space align="center">
            <Text>Monthly</Text>
            <Switch
              checked={isYearly}
              onChange={setIsYearly}
              style={{ 
                background: isYearly ? '#00cc6c' : undefined 
              }}
            />
            <Text>Yearly</Text>
            <Badge count="2 months free" style={{ backgroundColor: '#00cc6c' }} />
          </Space>
        </div>
      </div>

      <Row gutter={[24, 24]} className="plans-grid">
        {plans.map((plan) => (
          <Col xs={24} sm={12} lg={6} key={plan.id}>
            <Card
              className={`plan-card ${isCurrentPlan(plan.plan_type) ? 'current-plan' : ''} ${
                isRecommended(plan.plan_type) ? 'recommended' : ''
              }`}
              bodyStyle={{ padding: '32px 24px' }}
            >
              {isRecommended(plan.plan_type) && (
                <div className="recommended-badge">
                  <Badge.Ribbon text="Most Popular" color="gold">
                    <div style={{ height: 20 }}></div>
                  </Badge.Ribbon>
                </div>
              )}
              
              {isCurrentPlan(plan.plan_type) && (
                <div className="current-badge">
                  <Tag color="green" icon={<CheckOutlined />}>
                    Current Plan
                  </Tag>
                </div>
              )}

              <div className="plan-header">
                <div 
                  className="plan-icon"
                  style={{ color: planColors[plan.plan_type as keyof typeof planColors] }}
                >
                  {planIcons[plan.plan_type as keyof typeof planIcons]}
                </div>
                <Title level={3} className="plan-name">
                  {plan.name}
                </Title>
                <div className="plan-price">
                  {formatPrice(plan.price)}
                </div>
              </div>

              <Divider />

              <div className="plan-features">
                <div className="feature-item">
                  <CheckOutlined className="feature-icon" />
                  <span>{formatLimit(plan.influencer_limit, 'influencers')}</span>
                </div>
                <div className="feature-item">
                  <CheckOutlined className="feature-icon" />
                  <span>{formatLimit(plan.posts_per_month, 'posts/month')}</span>
                </div>
                <div className="feature-item">
                  <ClockCircleOutlined className="feature-icon" />
                  <span>{plan.analytics_retention_days} days data retention</span>
                </div>
                
                {plan.features.map((feature, index) => (
                  <div key={index} className="feature-item">
                    <CheckOutlined className="feature-icon" />
                    <span>{featureDescriptions[feature] || feature}</span>
                  </div>
                ))}
              </div>

              <div className="plan-action">
                {isCurrentPlan(plan.plan_type) ? (
                  <Button 
                    size="large" 
                    block 
                    disabled
                    icon={<SafetyCertificateOutlined />}
                  >
                    Current Plan
                  </Button>
                ) : (
                  <Button
                    type="primary"
                    size="large"
                    block
                    onClick={() => handleUpgrade(plan)}
                    style={{
                      background: planColors[plan.plan_type as keyof typeof planColors],
                      borderColor: planColors[plan.plan_type as keyof typeof planColors],
                    }}
                  >
                    {plan.plan_type === 'free' ? 'Get Started' : 'Upgrade Now'}
                  </Button>
                )}
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <div className="plans-footer">
        <Card className="guarantee-card">
          <Row align="middle" gutter={16}>
            <Col>
              <SafetyCertificateOutlined style={{ fontSize: 32, color: '#00cc6c' }} />
            </Col>
            <Col flex={1}>
              <Title level={4} style={{ margin: 0 }}>
                30-Day Money-Back Guarantee
              </Title>
              <Text type="secondary">
                Try any paid plan risk-free. If you're not satisfied, we'll refund your money.
              </Text>
            </Col>
          </Row>
        </Card>
      </div>

      {/* Upgrade Confirmation Modal */}
      <Modal
        title={`Upgrade to ${selectedPlan?.name}`}
        open={upgradeModalVisible}
        onCancel={() => setUpgradeModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setUpgradeModalVisible(false)}>
            Cancel
          </Button>,
          <Button key="confirm" type="primary" onClick={confirmUpgrade}>
            Confirm Upgrade
          </Button>
        ]}
      >
        {selectedPlan && (
          <div className="upgrade-confirmation">
            <div className="plan-summary">
              <div className="plan-info">
                <div 
                  className="plan-icon"
                  style={{ 
                    color: planColors[selectedPlan.plan_type as keyof typeof planColors],
                    fontSize: 24
                  }}
                >
                  {planIcons[selectedPlan.plan_type as keyof typeof planIcons]}
                </div>
                <div>
                  <Title level={4} style={{ margin: 0 }}>
                    {selectedPlan.name}
                  </Title>
                  <Text type="secondary">
                    {formatPrice(selectedPlan.price)}
                  </Text>
                </div>
              </div>
            </div>

            <Divider />

            <div className="billing-details">
              <Title level={5}>What you'll get:</Title>
              <ul>
                <li>{formatLimit(selectedPlan.influencer_limit, 'influencers')}</li>
                <li>{formatLimit(selectedPlan.posts_per_month, 'posts per month')}</li>
                <li>{selectedPlan.analytics_retention_days} days data retention</li>
                {selectedPlan.features.map((feature, index) => (
                  <li key={index}>
                    {featureDescriptions[feature] || feature}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default SubscriptionPlans;