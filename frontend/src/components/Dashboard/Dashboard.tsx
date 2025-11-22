import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import DashboardNavigation from '../Navigation/DashboardNavigation';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const { user, logout, hasRole, isAdmin, isAnalyst } = useAuth();

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
    <DashboardNavigation>
      <main className="dashboard-content">
        <div className="dashboard-grid">
          {/* User Profile Card */}
          <div className="dashboard-card">
            <h3>Profile Information</h3>
            <div className="profile-info">
              <p><strong>Name:</strong> {user.full_name}</p>
              <p><strong>Email:</strong> {user.email}</p>
              <p><strong>Role:</strong> {user.role}</p>
              <p><strong>Status:</strong> {user.is_active ? 'Active' : 'Inactive'}</p>
              <p><strong>Email Verified:</strong> {user.email_verified ? 'Yes' : 'No'}</p>
              <p><strong>Last Login:</strong> {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</p>
            </div>
          </div>

          {/* Role-based Access Demo */}
          <div className="dashboard-card">
            <h3>Access Levels</h3>
            <div className="access-info">
              <div className={`access-item ${hasRole('guest') ? 'granted' : 'denied'}`}>
                <span>Guest Access</span>
                <span>{hasRole('guest') ? '✅' : '❌'}</span>
              </div>
              <div className={`access-item ${isAnalyst() ? 'granted' : 'denied'}`}>
                <span>Analyst Access</span>
                <span>{isAnalyst() ? '✅' : '❌'}</span>
              </div>
              <div className={`access-item ${isAdmin() ? 'granted' : 'denied'}`}>
                <span>Admin Access</span>
                <span>{isAdmin() ? '✅' : '❌'}</span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="dashboard-card">
            <h3>Quick Actions</h3>
            <div className="actions-grid">
              <button className="action-button guest">
                View Videos
              </button>
              
              {isAnalyst() && (
                <button className="action-button analyst">
                  Analyze Data
                </button>
              )}
              
              {isAdmin() && (
                <>
                  <button className="action-button admin">
                    Manage Users
                  </button>
                  <button className="action-button admin">
                    System Settings
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Statistics (placeholder) */}
          <div className="dashboard-card">
            <h3>Statistics</h3>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-number">42</span>
                <span className="stat-label">Videos Tracked</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">128</span>
                <span className="stat-label">Objects Detected</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">96%</span>
                <span className="stat-label">Accuracy</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </DashboardNavigation>
  );
};

export default Dashboard;