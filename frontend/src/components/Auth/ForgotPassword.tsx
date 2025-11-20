import React, { useState } from 'react';
import authService from '../../services/authService';
import PolitikosLogo from '../Brand/PolitikosLogo';
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
          <PolitikosLogo size="large" withProtection={true} className="auth-logo" />
          <h2 className="auth-title">Esqueceu sua Senha?</h2>
          <p className="auth-subtitle">Digite seu email para redefinir sua senha</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email" className="form-label">
              Endereço de Email
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="form-input"
              placeholder="Digite seu email"
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
              'Enviar Instruções'
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p className="auth-switch">
            Lembrou sua senha?{' '}
            <button
              type="button"
              onClick={onSwitchToLogin}
              className="link-button"
            >
              Voltar ao login
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;