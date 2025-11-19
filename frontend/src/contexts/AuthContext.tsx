import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import authService from '../services/authService';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: string;
  is_active: boolean;
  email_verified: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  signup: (email: string, password: string, firstName: string, lastName: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
  hasRole: (role: string) => boolean;
  isAdmin: () => boolean;
  isAnalyst: () => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize authentication state
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      setLoading(true);
      
      // Check if user is already authenticated
      if (authService.isAuthenticated()) {
        // Try to get current user info
        const currentUser = await authService.getCurrentUser();
        if (currentUser) {
          setUser(currentUser);
        } else {
          // If unable to get user info, try using stored user data
          const storedUser = authService.getCurrentUserFromStorage();
          if (storedUser) {
            setUser(storedUser);
          } else {
            // Clear invalid tokens
            await authService.logout();
          }
        }
      }
    } catch (error) {
      console.error('Auth initialization error:', error);
      await authService.logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string, rememberMe: boolean = false) => {
    try {
      setLoading(true);
      setError(null);

      const response = await authService.login(email, password, rememberMe);
      
      if (response.success && response.user) {
        setUser(response.user);
      } else {
        throw new Error(response.message || 'Login failed');
      }
    } catch (error: any) {
      const errorMessage = error.message || 'An error occurred during login';
      setError(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (email: string, password: string, firstName: string, lastName: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await authService.signup(email, password, firstName, lastName);
      
      if (!response.success) {
        throw new Error(response.message || 'Signup failed');
      }

      // After successful signup, you might want to automatically log in
      // or redirect to login page. For now, we'll just show success message.
      
    } catch (error: any) {
      let errorMessage = 'An error occurred during signup';
      
      if (error.message) {
        errorMessage = error.message;
      } else if (typeof error === 'object' && error.details) {
        // Handle validation errors
        const details = error.details;
        if (typeof details === 'object') {
          const firstError = Object.values(details)[0];
          if (Array.isArray(firstError)) {
            errorMessage = firstError[0];
          } else if (typeof firstError === 'string') {
            errorMessage = firstError;
          }
        }
      }
      
      setError(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      setLoading(true);
      await authService.logout();
      setUser(null);
      setError(null);
    } catch (error) {
      console.error('Logout error:', error);
      // Even if logout request fails, clear local state
      setUser(null);
      setError(null);
    } finally {
      setLoading(false);
    }
  };

  const refreshUser = async () => {
    try {
      if (authService.isAuthenticated()) {
        const currentUser = await authService.getCurrentUser();
        if (currentUser) {
          setUser(currentUser);
        }
      }
    } catch (error) {
      console.error('Refresh user error:', error);
    }
  };

  const clearError = () => {
    setError(null);
  };

  const hasRole = (role: string): boolean => {
    return authService.hasRole(role);
  };

  const isAdmin = (): boolean => {
    return authService.isAdmin();
  };

  const isAnalyst = (): boolean => {
    return authService.isAnalyst();
  };

  const value: AuthContextType = {
    user,
    loading,
    error,
    isAuthenticated: authService.isAuthenticated() && !!user,
    login,
    signup,
    logout,
    refreshUser,
    clearError,
    hasRole,
    isAdmin,
    isAnalyst,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;