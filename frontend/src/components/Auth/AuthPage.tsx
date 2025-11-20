import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Login from './Login';
import Signup from './Signup';
import ForgotPassword from './ForgotPassword';

type AuthMode = 'login' | 'signup' | 'forgot-password';

const AuthPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Determine auth mode from URL
  const getAuthModeFromPath = (pathname: string): AuthMode => {
    if (pathname === '/signup') return 'signup';
    if (pathname === '/forgot-password') return 'forgot-password';
    return 'login';
  };
  
  const [authMode, setAuthMode] = useState<AuthMode>(getAuthModeFromPath(location.pathname));

  // Update auth mode when URL changes
  useEffect(() => {
    setAuthMode(getAuthModeFromPath(location.pathname));
  }, [location.pathname]);

  const handleSwitchToLogin = () => navigate('/login');
  const handleSwitchToSignup = () => navigate('/signup');
  const handleSwitchToForgotPassword = () => navigate('/forgot-password');

  return (
    <>
      {authMode === 'login' && (
        <Login
          onSwitchToSignup={handleSwitchToSignup}
          onSwitchToForgotPassword={handleSwitchToForgotPassword}
        />
      )}
      {authMode === 'signup' && (
        <Signup onSwitchToLogin={handleSwitchToLogin} />
      )}
      {authMode === 'forgot-password' && (
        <ForgotPassword onSwitchToLogin={handleSwitchToLogin} />
      )}
    </>
  );
};

export default AuthPage;