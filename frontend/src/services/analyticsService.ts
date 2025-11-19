import axios from 'axios';
import { authService } from './authService';

const API_BASE_URL = 'http://localhost:5000/api';

class AnalyticsService {
  private api = axios.create({
    baseURL: `${API_BASE_URL}/analytics`,
  });

  constructor() {
    // Add auth interceptor
    this.api.interceptors.request.use((config) => {
      const token = authService.getToken();
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

  // Dashboard data
  async getDashboard() {
    const response = await this.api.get('/dashboard');
    return response.data;
  }

  // Influencer analytics
  async analyzeInfluencer(influencerId: number, daysBack: number = 30) {
    const response = await this.api.post(`/influencer/${influencerId}/analyze`, {
      days_back: daysBack
    });
    return response.data;
  }

  async getInfluencerAnalytics(influencerId: number) {
    const response = await this.api.get(`/influencer/${influencerId}/analytics`);
    return response.data;
  }

  // Sentiment analysis
  async analyzePostSentiment(postId: number) {
    const response = await this.api.post(`/sentiment/posts/${postId}`);
    return response.data;
  }

  async analyzeCommentSentiment(commentId: number) {
    const response = await this.api.post(`/sentiment/comments/${commentId}`);
    return response.data;
  }

  async processBulkSentiment(batchSize: number = 100) {
    const response = await this.api.post('/sentiment/bulk', {
      batch_size: batchSize
    });
    return response.data;
  }

  async getSentimentOverview(daysBack: number = 7, platform?: string) {
    const params: any = { days_back: daysBack };
    if (platform) params.platform = platform;
    
    const response = await this.api.get('/sentiment/overview', { params });
    return response.data;
  }

  // Trending topics
  async getTrendingTopics(hoursBack: number = 24, limit: number = 50) {
    const response = await this.api.get('/trending', {
      params: { hours_back: hoursBack, limit }
    });
    return response.data;
  }

  async detectTrendingTopics(hoursBack: number = 24) {
    const response = await this.api.post('/trending/detect', {
      hours_back: hoursBack
    });
    return response.data;
  }

  // Leaderboard
  async getInfluenceLeaderboard(platform?: string, limit: number = 50, daysBack: number = 7) {
    const params: any = { limit, days_back: daysBack };
    if (platform) params.platform = platform;
    
    const response = await this.api.get('/leaderboard', { params });
    return response.data;
  }

  // Keywords
  async getInfluencerKeywords(influencerId: number) {
    const response = await this.api.get(`/keywords/${influencerId}`);
    return response.data;
  }

  // Export
  async exportInfluencerAnalytics(
    influencerId: number, 
    format: string = 'json', 
    daysBack: number = 30
  ) {
    const response = await this.api.get(`/export/${influencerId}`, {
      params: { format, days_back: daysBack }
    });
    return response.data;
  }

  // Error handling utility
  private handleError(error: any) {
    console.error('Analytics service error:', error);
    if (error.response) {
      throw new Error(error.response.data.error || 'Analytics request failed');
    } else if (error.request) {
      throw new Error('Network error - please check your connection');
    } else {
      throw new Error('Request failed');
    }
  }
}

export const analyticsService = new AnalyticsService();