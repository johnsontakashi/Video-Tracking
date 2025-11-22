import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Menu, Layout, Button, Avatar, Dropdown } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  BarChartOutlined,
  TeamOutlined,
  CrownOutlined,
  LogoutOutlined,
  SettingOutlined,
  BellOutlined,
  PlusOutlined
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import PolitikosLogo, { PolitikosLogoText } from '../Brand/PolitikosLogo';
import './DashboardNavigation.css';

const { Header, Sider } = Layout;

interface DashboardNavigationProps {
  children: React.ReactNode;
}

const DashboardNavigation: React.FC<DashboardNavigationProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  // Get menu items based on user role
  const getMenuItems = () => {
    const baseItems = [
      {
        key: '/dashboard',
        icon: <DashboardOutlined />,
        label: 'Dashboard'
      },
      {
        key: '/influencers',
        icon: <TeamOutlined />,
        label: 'Influencers'
      },
      {
        key: '/analytics',
        icon: <BarChartOutlined />,
        label: 'Analytics'
      },
      {
        key: '/subscription',
        icon: <CrownOutlined />,
        label: 'Subscription'
      }
    ];

    // Add admin-only items
    if (user?.role === 'admin') {
      baseItems.push({
        key: '/users',
        icon: <SettingOutlined />,
        label: 'User Management'
      });
    }

    return baseItems;
  };

  // Handle menu click
  const handleMenuClick = (e: any) => {
    navigate(e.key);
  };

  // Handle dropdown menu clicks
  const handleDropdownClick = (e: any) => {
    if (e.key === 'logout') {
      handleLogout();
    } else if (e.key === 'profile') {
      // Handle profile settings
      console.log('Profile settings clicked');
    } else if (e.key === 'notifications') {
      // Handle notifications
      console.log('Notifications clicked');
    }
  };

  // User dropdown menu
  const userMenu = {
    items: [
      {
        key: 'profile',
        icon: <UserOutlined />,
        label: 'Profile Settings',
      },
      {
        key: 'notifications',
        icon: <BellOutlined />,
        label: 'Notifications',
      },
      {
        type: 'divider' as const,
      },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: 'Logout',
      },
    ],
    onClick: handleDropdownClick,
  };

  const selectedKey = location.pathname;

  return (
    <Layout className="dashboard-layout">
      <Header className="dashboard-header">
        <div className="header-left">
          <PolitikosLogoText size="large" className="dashboard-logo" />
          <div className="dashboard-title">
            <h1>Video Tracking Platform</h1>
            <span className="dashboard-subtitle">Influencer Analytics & Management</span>
          </div>
        </div>

        <div className="header-center">
          <Menu
            mode="horizontal"
            selectedKeys={[selectedKey]}
            items={getMenuItems()}
            className="header-menu"
            onClick={handleMenuClick}
          />
        </div>

        <div className="header-right">
          <Button
            type="primary"
            icon={<PlusOutlined />}
            className="add-button"
            onClick={() => {
              if (selectedKey === '/influencers') {
                // Trigger add influencer modal - will be handled by parent component
                const event = new CustomEvent('openAddModal');
                window.dispatchEvent(event);
              } else {
                navigate('/influencers');
              }
            }}
          >
            Add New
          </Button>

          <div className="user-info">
            <span className="welcome-text">Welcome, {user?.first_name}</span>
            <span className="user-role">{user?.role.toUpperCase()}</span>
          </div>

          <Button
            type="text"
            icon={<LogoutOutlined />}
            onClick={handleLogout}
            className="logout-button"
            title="Logout"
          >
            Logout
          </Button>

          <Dropdown menu={userMenu} placement="bottomRight">
            <Avatar
              size={40}
              icon={<UserOutlined />}
              className="user-avatar"
            />
          </Dropdown>
        </div>
      </Header>

      <Layout>
        <div className="dashboard-content">
          {children}
        </div>
      </Layout>
    </Layout>
  );
};

export default DashboardNavigation;