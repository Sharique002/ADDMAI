/**
 * ADDMAI API Client Service.
 *
 * Conforms to Section 9 (Frontend API Service) and Section 10 (Configuration).
 * Isolates HTTP transport logic from UI components.
 */

import {
  HealthResponse,
  MediaIngestionResponse,
  ReadyResponse,
} from '../types';

// Configurable API base URL, defaulting to local development gateway
const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';

class ApiService {
  private readonly baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  /**
   * Check backend service liveness via GET /api/v1/health.
   */
  async checkHealth(): Promise<HealthResponse> {
    const url = `${this.baseUrl}/api/v1/health`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Health probe failed with status HTTP ${response.status}`);
    }

    return response.json();
  }

  /**
   * Check backend infrastructure readiness via GET /api/v1/ready.
   */
  async checkReadiness(): Promise<ReadyResponse> {
    const url = `${this.baseUrl}/api/v1/ready`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    });

    return response.json();
  }

  /**
   * Upload untrusted media asset via POST /api/v1/media (Section 31).
   */
  async uploadMedia(file: File): Promise<MediaIngestionResponse> {
    const url = `${this.baseUrl}/api/v1/media`;
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
      },
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      const errorMsg = data.detail || `Upload failed with status HTTP ${response.status}`;
      throw new Error(errorMsg);
    }

    return data as MediaIngestionResponse;
  }

  /**
   * Retrieve structured media record via GET /api/v1/media/{mediaId} (Section 31).
   */
  async getMedia(mediaId: string): Promise<MediaIngestionResponse> {
    const url = `${this.baseUrl}/api/v1/media/${encodeURIComponent(mediaId)}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    });

    const data = await response.json();
    if (!response.ok) {
      const errorMsg = data.detail || `Retrieval failed with status HTTP ${response.status}`;
      throw new Error(errorMsg);
    }

    return data as MediaIngestionResponse;
  }

  /**
   * Returns the currently configured API base URL.
   */
  getBaseUrl(): string {
    return this.baseUrl;
  }
}

export const apiService = new ApiService(API_BASE_URL);
export default apiService;

