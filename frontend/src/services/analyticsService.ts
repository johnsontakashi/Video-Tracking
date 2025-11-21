import axios from 'axios';
import { authService } from './authService';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

class AnalyticsService {
  private api = axios.create({
    baseURL: `${API_BASE_URL}/api/analytics`,
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

  // Dashboard data
  async getDashboard() {
    // Check if we should use mock data
    const useMockData = process.env.REACT_APP_USE_MOCK_DATA === 'true' || 
                       process.env.NODE_ENV === 'development';
    
    if (useMockData) {
      // Return mock dashboard data
      return {
        summary: {
          total_influencers: 1247,
          total_posts: 8456,
          total_engagement: 342567,
          avg_engagement_rate: 4.2,
          top_platforms: [
            { platform: 'Instagram', count: 520 },
            { platform: 'YouTube', count: 340 },
            { platform: 'TikTok', count: 287 },
            { platform: 'Twitter', count: 100 }
          ],
          engagement_trend: [
            { date: '2024-01-01', engagement: 12450 },
            { date: '2024-01-02', engagement: 13200 },
            { date: '2024-01-03', engagement: 11800 },
            { date: '2024-01-04', engagement: 14600 },
            { date: '2024-01-05', engagement: 15100 },
            { date: '2024-01-06', engagement: 13900 },
            { date: '2024-01-07', engagement: 16200 }
          ]
        },
        trending_topics: [
          { keyword: '#sustainability', velocity: 85, mentions: 1250 },
          { keyword: '#tech2024', velocity: 72, mentions: 980 },
          { keyword: '#wellness', velocity: 68, mentions: 890 }
        ],
        top_performers: [
          { username: 'techguru123', platform: 'instagram', influence_score: 92.4 },
          { username: 'fashionista_rio', platform: 'instagram', influence_score: 88.1 },
          { username: 'fitness_coach_sp', platform: 'youtube', influence_score: 85.7 }
        ]
      };
    }

    try {
      const response = await this.api.get('/dashboard');
      return response.data;
    } catch (error) {
      console.warn('Failed to fetch dashboard from backend, using mock data');
      throw new Error('BACKEND_UNAVAILABLE');
    }
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