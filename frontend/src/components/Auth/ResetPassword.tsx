import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import authService from '../../services/authService';
import PolitikosLogo from '../Brand/PolitikosLogo';
import './Auth.css';

interface ResetPasswordFormData {
  newPassword: string;
  confirmPassword: string;
}

interface ResetPasswordProps {
  onSwitchToLogin?: () => void;
}

const ResetPassword: React.FC<ResetPasswordProps> = ({ onSwitchToLogin }) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  
  const [formData, setFormData] = useState<ResetPasswordFormData>({
    newPassword: '',
    confirmPassword: ''
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [validatingToken, setValidatingToken] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // Validate token on component mount
  useEffect(() => {
    const validateToken = async () => {
      if (!token) {
        setError('Token de redefinição não encontrado');
        setValidatingToken(false);
        return;
      }

      try {
        const response = await authService.validateResetToken(token);
        if (response.success) {
          setTokenValid(true);
          setUserEmail(response.user_email || '');
        } else {
          setError(response.message || 'Token inválido ou expirado');
        }
      } catch (error: any) {
        setError('Erro ao validar token');
      } finally {
        setValidatingToken(false);
      }
    };

    validateToken();
  }, [token]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear validation error when user starts typing
    if (validationErrors[name]) {
      setValidationErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const getPasswordStrength = (password: string): string => {
    if (password.length === 0) return '';
    if (password.length < 8) return 'weak';
    if (password.length < 12) return 'medium';
    return 'strong';
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.newPassword) {
      errors.newPassword = 'Nova senha é obrigatória';
    } else {
      if (formData.newPassword.length < 8) {
        errors.newPassword = 'Senha deve ter pelo menos 8 caracteres';
      } else if (!/(?=.*[a-z])/.test(formData.newPassword)) {
        errors.newPassword = 'Senha deve conter pelo menos uma letra minúscula';
      } else if (!/(?=.*[A-Z])/.test(formData.newPassword)) {
        errors.newPassword = 'Senha deve conter pelo menos uma letra maiúscula';
      } else if (!/(?=.*\d)/.test(formData.newPassword)) {
        errors.newPassword = 'Senha deve conter pelo menos um número';
      }
    }

    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Confirmação de senha é obrigatória';
    } else if (formData.newPassword !== formData.confirmPassword) {
      errors.confirmPassword = 'Senhas não coincidem';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!validateForm()) {
      return;
    }

    if (!token) {
      setError('Token de redefinição não encontrado');
      return;
    }

    setLoading(true);

    try {
      const response = await authService.resetPassword(token, formData.newPassword);
      
      if (response.success) {
        setSuccess('Senha redefinida com sucesso! Você será redirecionado para o login.');
        // Redirect to login after 3 seconds
        setTimeout(() => {
          if (onSwitchToLogin) {
            onSwitchToLogin();
          } else {
            navigate('/login');
          }
        }, 3000);
      } else {
        setError(response.message || 'Erro ao redefinir senha');
      }
    } catch (error: any) {
      setError('Erro ao redefinir senha. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleBackToLogin = () => {
    if (onSwitchToLogin) {
      onSwitchToLogin();
    } else {
      navigate('/login');
    }
  };

  const passwordStrength = getPasswordStrength(formData.newPassword);

  // Show loading state while validating token
  if (validatingToken) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <PolitikosLogo size="large" withProtection={true} className="auth-logo" />
            <h2 className="auth-title">Validando Token...</h2>
            <p className="auth-subtitle">Aguarde enquanto validamos seu token de redefinição</p>
          </div>
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <span className="loading-spinner">⌛</span>
          </div>
        </div>
      </div>
    );
  }

  // Show error if token is invalid
  if (!tokenValid) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <PolitikosLogo size="large" withProtection={true} className="auth-logo" />
            <h2 className="auth-title">Token Inválido</h2>
            <p className="auth-subtitle">Não foi possível validar seu token de redefinição</p>
          </div>

          {error && (
            <div className="error-message" style={{ margin: '20px 0' }}>
              {error}
            </div>
          )}

          <div className="auth-form">
            <p style={{ textAlign: 'center', color: '#4a4a4a', marginBottom: '20px' }}>
              O token pode ter expirado ou já ter sido utilizado. 
              Solicite uma nova redefinição de senha.
            </p>
            
            <button
              type="button"
              onClick={handleBackToLogin}
              className="submit-button"
              style={{ width: '100%' }}
            >
              Voltar ao Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Show reset password form
  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <PolitikosLogo size="large" withProtection={true} className="auth-logo" />
          <h2 className="auth-title">Redefinir Senha</h2>
          <p className="auth-subtitle">
            {userEmail ? `Redefinindo senha para: ${userEmail}` : 'Crie sua nova senha'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="newPassword" className="form-label">
                Nova Senha
              </label>
              <div className="password-input-container">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="newPassword"
                  name="newPassword"
                  value={formData.newPassword}
                  onChange={handleChange}
                  required
                  className={`form-input ${validationErrors.newPassword ? 'error' : ''}`}
                  placeholder="Digite sua nova senha"
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="password-toggle"
                >
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>
              {passwordStrength && (
                <div className={`password-strength ${passwordStrength}`}>
                  Força da senha: <span>{passwordStrength === 'weak' ? 'Fraca' : passwordStrength === 'medium' ? 'Média' : 'Forte'}</span>
                </div>
              )}
              {validationErrors.newPassword && (
                <span className="field-error">{validationErrors.newPassword}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword" className="form-label">
                Confirmar Nova Senha
              </label>
              <div className="password-input-container">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  id="confirmPassword"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  required
                  className={`form-input ${validationErrors.confirmPassword ? 'error' : ''}`}
                  placeholder="Confirme sua nova senha"
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="password-toggle"
                >
                  {showConfirmPassword ? '🙈' : '👁️'}
                </button>
              </div>
              {validationErrors.confirmPassword && (
                <span className="field-error">{validationErrors.confirmPassword}</span>
              )}
            </div>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {success && (
            <div className="success-message">
              {success}
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
              'Redefinir Senha'
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p className="auth-switch">
            Lembrou sua senha?{' '}
            <button
              type="button"
              onClick={handleBackToLogin}
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

export default ResetPassword;