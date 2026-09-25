/**
 * Type definitions for ADDMAI Web Client.
 */

export interface HealthResponse {
  status: string;
}

export interface DependencyStatus {
  configured: boolean;
  status: 'ready' | 'not_ready' | 'pending';
}

export interface ReadyResponse {
  status: 'ready' | 'not_ready' | string;
  dependencies: Record<string, DependencyStatus>;
  timestamp: string;
}
