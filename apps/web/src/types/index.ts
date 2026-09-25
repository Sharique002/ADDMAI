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

export interface IntegrityRecord {
  sha256_digest: string;
  algorithm: string;
  size_bytes: number;
  verified: boolean;
  note: string;
}

export interface EvidenceItem {
  evidence_type: string;
  source: string;
  value: any;
  observed_at: string;
}

export interface AnalysisRecord {
  media_id: string;
  ingestion: {
    media_id: string;
    sha256_digest: string;
    media_category: string;
    mime_type: string;
    original_filename: string;
    size_bytes: number;
    validation_status: string;
    created_at: string;
  };
  integrity: IntegrityRecord;
  container: Record<string, any>;
  metadata: Record<string, any>;
  evidence: EvidenceItem[];
}

export interface MediaIngestionResponse {
  media_id: string;
  sha256_digest: string;
  media_category: string;
  mime_type: string;
  original_filename: string;
  size_bytes: number;
  validation_status: string;
  created_at: string;
  is_duplicate: boolean;
  analysis?: AnalysisRecord;
}

export interface MediaErrorResponse {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
}

export interface ModelInfo {
  model_id: string;
  version: string;
}

export interface ModelPredictionResponse {
  media_id: string;
  model: ModelInfo;
  prediction: 'REAL' | 'DEEPFAKE';
  confidence: number;
  preprocessing_version: string;
  inference_timestamp: string;
  prediction_id?: string;
  model_artifact_sha256?: string;
}


