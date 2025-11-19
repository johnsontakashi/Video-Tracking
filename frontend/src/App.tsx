import React from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AuthPage from './components/Auth/AuthPage';
import Dashboard from './components/Dashboard/Dashboard';
import './App.css';

// Loading component
const LoadingScreen: React.FC = () => (
  <div className="loading-overlay">
    <div className="loading-card">
      <div className="loading-spinner">⌛</div>
      <div className="loading-text">Loading...</div>
    </div>
  </div>
);

// Main app content component
const AppContent: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  return isAuthenticated ? <Dashboard /> : <AuthPage />;
};

// Main App component
function App() {
  return (
    <AuthProvider>
      <div className="App">
        <AppContent />
      </div>
    </AuthProvider>
  );
}

export default App;
