import axios from 'axios';
import { authService } from './authService';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

class PaymentService {
  private api = axios.create({
    baseURL: `${API_BASE_URL}/api/payment`,
  });

  constructor() {
    // Add auth interceptor
    this.api.interceptors.request.use((config) => {
      const token = authService.getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Add response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          authService.logout();
          window.location.href = '/login';
        }
        throw error;
      }
    );
  }

  // Health check
  async getHealth() {
    const response = await this.api.get('/health');
    return response.data;
  }

  // Plans (public endpoint)
  async getPlans() {
    // In development, check if backend is available first
    if (process.env.NODE_ENV === 'development') {
      try {
        const healthCheck = await axios.get(`${API_BASE_URL}/api/health`, {
          timeout: 1000,
          // Suppress axios error logging for this check
          transformRequest: [(data, headers) => {
            delete headers['X-Requested-With'];
            return data;
          }]
        });
        if (!healthCheck.data) {
          throw new Error('BACKEND_UNAVAILABLE');
        }
      } catch (error) {
        // Backend is not available, fail silently
        throw new Error('BACKEND_UNAVAILABLE');
      }
    }

    try {
      const response = await axios.get(`${API_BASE_URL}/api/payment/plans`, {
        timeout: process.env.NODE_ENV === 'development' ? 2000 : 10000
      });
      return response.data;
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        throw new Error('BACKEND_UNAVAILABLE');
      }
      throw error;
    }
  }

  // Subscription info
  async getSubscriptionInfo() {
    const response = await this.api.get('/subscription/info');
    return response.data;
  }

  // Create payment intent
  async createPaymentIntent(planType: string, paymentMethod?: any) {
    const response = await this.api.post('/payment-intent', {
      plan_type: planType,
      payment_method: paymentMethod
    });
    return response.data;
  }

  // Create subscription
  async createSubscription(planType: string) {
    const response = await this.api.post('/subscription/create', {
      plan_type: planType
    });
    return response.data;
  }

  // Cancel subscription
  async cancelSubscription() {
    const response = await this.api.post('/subscription/cancel');
    return response.data;
  }

  // Confirm payment
  async confirmPayment(paymentIntentId: string) {
    const response = await this.api.post('/payment/confirm', {
      payment_intent_id: paymentIntentId
    });
    return response.data;
  }

  // Get payments history
  async getPayments(page: number = 1, perPage: number = 20) {
    const response = await this.api.get('/payments', {
      params: { page, per_page: perPage }
    });
    return response.data;
  }

  // Get subscriptions history
  async getSubscriptions(page: number = 1, perPage: number = 20) {
    const response = await this.api.get('/subscriptions', {
      params: { page, per_page: perPage }
    });
    return response.data;
  }

  // Get usage statistics
  async getUsageStats() {
    const response = await this.api.get('/usage');
    return response.data;
  }

  // Create billing portal session
  async createBillingPortal(returnUrl?: string) {
    const response = await this.api.post('/billing/portal', {
      return_url: returnUrl
    });
    return response.data;
  }

  // Error handling utility
  private handleError(error: any) {
    console.error('Payment service error:', error);
    if (error.response) {
      throw new Error(error.response.data.error || 'Payment request failed');
    } else if (error.request) {
      throw new Error('Network error - please check your connection');
    } else {
      throw new Error('Request failed');
    }
  }
}

export const paymentService = new PaymentService();