import React, { useState } from 'react';
import Login from './Login';
import Signup from './Signup';
import ForgotPassword from './ForgotPassword';

type AuthMode = 'login' | 'signup' | 'forgot-password';

const AuthPage: React.FC = () => {
  const [authMode, setAuthMode] = useState<AuthMode>('login');

  const handleSwitchToLogin = () => setAuthMode('login');
  const handleSwitchToSignup = () => setAuthMode('signup');
  const handleSwitchToForgotPassword = () => setAuthMode('forgot-password');

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