interface LoginRequest {
  email: string;
  password: string;
  rememberMe?: boolean;
}

interface SignupRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role?: string;
}

interface AuthResponse {
  success: boolean;
  access_token?: string;
  refresh_token?: string;
  token_type?: string;
  expires_in?: number;
  user?: any;
  error?: string;
  message?: string;
  details?: any;
}

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

class AuthService {
  private baseURL: string;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
    this.loadTokensFromStorage();
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const defaultHeaders: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (this.accessToken) {
      defaultHeaders['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401 && this.refreshToken) {
          // Try to refresh token
          const refreshed = await this.refreshAccessToken();
          if (refreshed) {
            // Retry the original request with new token
            config.headers = {
              ...config.headers,
              'Authorization': `Bearer ${this.accessToken}`,
            };
            const retryResponse = await fetch(url, config);
            return await retryResponse.json();
          } else {
            // Refresh failed, logout user
            this.logout();
            throw new Error('Session expired. Please login again.');
          }
        }
        
        throw new Error(data.message || `HTTP error! status: ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }

  private saveTokensToStorage(accessToken: string, refreshToken: string): void {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    
    // Store in localStorage for persistence
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    
    // Also store in secure httpOnly cookie if possible (via backend)
    // For now, we'll use localStorage with additional security measures
  }

  private loadTokensFromStorage(): void {
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  private clearTokensFromStorage(): void {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  async login(email: string, password: string, rememberMe: boolean = false): Promise<AuthResponse> {
    try {
      const response: AuthResponse = await this.request('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          email,
          password,
          remember_me: rememberMe,
        }),
      });

      if (response.success && response.access_token && response.refresh_token) {
        this.saveTokensToStorage(response.access_token, response.refresh_token);
        
        // Store user info
        if (response.user) {
          localStorage.setItem('user', JSON.stringify(response.user));
        }
      }

      return response;
    } catch (error) {
      throw error;
    }
  }

  async signup(email: string, password: string, firstName: string, lastName: string): Promise<AuthResponse> {
    try {
      const response: AuthResponse = await this.request('/api/auth/signup', {
        method: 'POST',
        body: JSON.stringify({
          email,
          password,
          first_name: firstName,
          last_name: lastName,
          role: 'guest',
        }),
      });

      return response;
    } catch (error) {
      throw error;
    }
  }

  async refreshAccessToken(): Promise<boolean> {
    if (!this.refreshToken) {
      return false;
    }

    try {
      const response: AuthResponse = await this.request('/api/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({
          refresh_token: this.refreshToken,
        }),
      });

      if (response.success && response.access_token) {
        this.accessToken = response.access_token;
        localStorage.setItem('access_token', response.access_token);
        
        // Update user info if provided
        if (response.user) {
          localStorage.setItem('user', JSON.stringify(response.user));
        }
        
        return true;
      }

      return false;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  }

  async logout(): Promise<void> {
    try {
      if (this.refreshToken) {
        await this.request('/api/auth/logout', {
          method: 'POST',
          body: JSON.stringify({
            refresh_token: this.refreshToken,
          }),
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.clearTokensFromStorage();
    }
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      const response: any = await this.request('/api/auth/me');
      
      if (response.success && response.user) {
        localStorage.setItem('user', JSON.stringify(response.user));
        return response.user;
      }
      
      return null;
    } catch (error) {
      console.error('Get current user failed:', error);
      return null;
    }
  }

  async requestPasswordReset(email: string): Promise<AuthResponse> {
    try {
      const response: AuthResponse = await this.request('/api/auth/request-password-reset', {
        method: 'POST',
        body: JSON.stringify({ email }),
      });

      return response;
    } catch (error) {
      throw error;
    }
  }

  async resetPassword(token: string, newPassword: string): Promise<AuthResponse> {
    try {
      const response: AuthResponse = await this.request('/api/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify({
          token,
          new_password: newPassword,
        }),
      });

      return response;
    } catch (error) {
      throw error;
    }
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<AuthResponse> {
    try {
      const response: AuthResponse = await this.request('/api/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      return response;
    } catch (error) {
      throw error;
    }
  }

  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  getCurrentUserFromStorage(): User | null {
    try {
      const userStr = localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      return null;
    }
  }

  hasRole(requiredRole: string): boolean {
    const user = this.getCurrentUserFromStorage();
    if (!user) return false;

    const roleHierarchy: Record<string, number> = {
      guest: 1,
      analyst: 2,
      admin: 3,
    };

    const userRoleLevel = roleHierarchy[user.role] || 0;
    const requiredRoleLevel = roleHierarchy[requiredRole] || 0;

    return userRoleLevel >= requiredRoleLevel;
  }

  isAdmin(): boolean {
    return this.hasRole('admin');
  }

  isAnalyst(): boolean {
    return this.hasRole('analyst');
  }
}

// Export singleton instance
export const authService = new AuthService();
export default authService;