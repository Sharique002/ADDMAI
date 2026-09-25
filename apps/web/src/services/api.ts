/**
 * ADDMAI API Client Service.
 *
 * Conforms to Section 9 (Frontend API Service) and Section 10 (Configuration).
 * Isolates HTTP transport logic from UI components.
 */

import { HealthResponse, ReadyResponse } from '../types';

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
   * Returns the currently configured API base URL.
   */
  getBaseUrl(): string {
    return this.baseUrl;
  }
}

export const apiService = new ApiService(API_BASE_URL);
export default apiService;
