import React, { useState } from 'react';
import authService from '../../services/authService';
import './Auth.css';

interface ForgotPasswordProps {
  onSwitchToLogin: () => void;
}

const ForgotPassword: React.FC<ForgotPasswordProps> = ({ onSwitchToLogin }) => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await authService.requestPasswordReset(email);
      
      if (response.success) {
        setMessage(response.message || 'Password reset instructions have been sent to your email.');
      } else {
        setError(response.message || 'Failed to request password reset');
      }
    } catch (error: any) {
      setError(error.message || 'An error occurred while requesting password reset');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h2 className="auth-title">Forgot Password</h2>
          <p className="auth-subtitle">Enter your email to reset your password</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email" className="form-label">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="form-input"
              placeholder="Enter your email"
              autoComplete="email"
            />
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {message && (
            <div className="success-message">
              {message}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="submit-button"
          >
            {loading ? (
              <span className="loading-spinner">⌛</span>
            ) : (
              'Send Reset Instructions'
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p className="auth-switch">
            Remember your password?{' '}
            <button
              type="button"
              onClick={onSwitchToLogin}
              className="link-button"
            >
              Back to sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;