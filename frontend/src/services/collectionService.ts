import axios from 'axios';
import { authService } from './authService';

const API_BASE_URL = 'http://localhost:5000/api';

interface CreateInfluencerData {
  username: string;
  platform: string;
  external_id?: string;
  display_name?: string;
  bio?: string;
  priority_score?: number;
}

interface CollectionTaskParams {
  force?: boolean;
  include_posts?: boolean;
  posts_limit?: number;
  limit?: number;
}

class CollectionService {
  private api = axios.create({
    baseURL: `${API_BASE_URL}/collection`,
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

  // Influencer management
  async createInfluencer(data: CreateInfluencerData) {
    const response = await this.api.post('/influencers', data);
    return response.data;
  }

  async getInfluencers(page: number = 1, perPage: number = 20, platform?: string) {
    const params: any = { page, per_page: perPage };
    if (platform) params.platform = platform;
    
    const response = await this.api.get('/influencers', { params });
    return response.data;
  }

  // Data collection
  async collectInfluencerData(influencerId: number, params: CollectionTaskParams = {}) {
    const response = await this.api.post(`/influencers/${influencerId}/collect`, params);
    return response.data;
  }

  async collectPostComments(postId: number, limit: number = 100) {
    const response = await this.api.post(`/posts/${postId}/comments/collect`, {
      limit
    });
    return response.data;
  }

  // Task management
  async getCollectionTasks(
    page: number = 1, 
    perPage: number = 20, 
    filters: {
      status?: string;
      platform?: string;
      influencer_id?: number;
    } = {}
  ) {
    const params: any = { page, per_page: perPage, ...filters };
    const response = await this.api.get('/tasks', { params });
    return response.data;
  }

  async processPendingTasks(maxTasks: number = 10) {
    const response = await this.api.post('/tasks/process', {
      max_tasks: maxTasks
    });
    return response.data;
  }

  // Statistics
  async getCollectionStats() {
    const response = await this.api.get('/stats');
    return response.data;
  }

  // Scheduling
  async scheduleCollection(influencerIds: number[], priority: string = 'normal') {
    const response = await this.api.post('/schedule', {
      influencer_ids: influencerIds,
      priority
    });
    return response.data;
  }

  // Error handling utility
  private handleError(error: any) {
    console.error('Collection service error:', error);
    if (error.response) {
      throw new Error(error.response.data.error || 'Collection request failed');
    } else if (error.request) {
      throw new Error('Network error - please check your connection');
    } else {
      throw new Error('Request failed');
    }
  }
}

export const collectionService = new CollectionService();