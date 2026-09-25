import React, { useState } from 'react';
import apiService from './services/api';
import { HealthResponse, MediaIngestionResponse, ReadyResponse } from './types';

export const App: React.FC = () => {
  // System Health State
  const [healthStatus, setHealthStatus] = useState<HealthResponse | null>(null);
  const [readyStatus, setReadyStatus] = useState<ReadyResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(false);
  const [healthError, setHealthError] = useState<string | null>(null);

  // Ingestion State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [ingestionResult, setIngestionResult] = useState<MediaIngestionResponse | null>(null);

  // Lookup State
  const [lookupId, setLookupId] = useState<string>('');
  const [lookupLoading, setLookupLoading] = useState<boolean>(false);
  const [lookupError, setLookupError] = useState<string | null>(null);

  const runHealthCheck = async () => {
    setHealthLoading(true);
    setHealthError(null);
    try {
      const [health, ready] = await Promise.all([
        apiService.checkHealth(),
        apiService.checkReadiness(),
      ]);
      setHealthStatus(health);
      setReadyStatus(ready);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setHealthError(err.message);
      } else {
        setHealthError('Unable to connect to backend API');
      }
    } finally {
      setHealthLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setUploadError(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError('Please select a media file (JPEG, PNG, or MP4) to ingest.');
      return;
    }

    setUploadLoading(true);
    setUploadError(null);
    try {
      const result = await apiService.uploadMedia(selectedFile);
      setIngestionResult(result);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setUploadError(err.message);
      } else {
        setUploadError('Failed to ingest media file.');
      }
    } finally {
      setUploadLoading(false);
    }
  };

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lookupId.trim()) {
      setLookupError('Please enter a valid media_id UUID.');
      return;
    }

    setLookupLoading(true);
    setLookupError(null);
    try {
      const result = await apiService.getMedia(lookupId.trim());
      setIngestionResult(result);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setLookupError(err.message);
      } else {
        setLookupError('Media asset not found.');
      }
    } finally {
      setLookupLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#090d16', color: '#f8fafc' }}>
      {/* Header */}
      <header
        style={{
          borderBottom: '1px solid #1e293b',
          backgroundColor: '#0f172a',
          padding: '1.25rem 2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span
              style={{
                fontSize: '1.5rem',
                fontWeight: 800,
                letterSpacing: '0.05em',
                background: 'linear-gradient(to right, #38bdf8, #818cf8)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              ADDMAI
            </span>
            <span
              style={{
                fontSize: '0.75rem',
                padding: '0.2rem 0.6rem',
                borderRadius: '9999px',
                backgroundColor: '#1e293b',
                color: '#38bdf8',
                fontWeight: 600,
                border: '1px solid #334155',
              }}
            >
              Stage 2.1: Ingestion &amp; Integrity Hardening
            </span>
          </div>
          <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: '#94a3b8' }}>
            AI-Powered Deepfake Detection &amp; Media Authenticity Intelligence
          </p>
        </div>

        <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
          Gateway: <code style={{ color: '#38bdf8' }}>{apiService.getBaseUrl()}</code>
        </div>
      </header>

      {/* Main Content */}
      <main
        style={{
          flex: 1,
          maxWidth: '1080px',
          width: '100%',
          margin: '0 auto',
          padding: '2rem 1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '2rem',
        }}
      >
        {/* Notice Banner */}
        <div
          style={{
            backgroundColor: '#1e1b4b',
            border: '1px solid #4338ca',
            borderRadius: '0.5rem',
            padding: '1rem 1.25rem',
            color: '#c7d2fe',
            fontSize: '0.875rem',
            lineHeight: 1.5,
          }}
        >
          <strong>Stage 2.1 Status:</strong> Media Ingestion &amp; Integrity Hardened. Hostile media validation, strict magic-byte signatures, bounded upload streaming (25 MB inclusive), immutable SHA-256 integrity, canonical MinIO storage deduplication, and PostgreSQL constraint enforcement.
          <div style={{ marginTop: '0.35rem', color: '#94a3b8', fontSize: '0.8rem' }}>
            <strong>Constitutional Rule:</strong> Stage 2.1 does NOT evaluate deepfake models or authenticity verdicts. Ingestion verifies cryptographic integrity and extracts neutral container properties only.
          </div>
        </div>


        {/* Media Ingestion Card (Section 30) */}
        <section
          style={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '0.75rem',
            padding: '1.75rem',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.2)',
          }}
        >
          <div style={{ marginBottom: '1.25rem' }}>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600, color: '#f8fafc' }}>
              Media Asset Ingestion
            </h2>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: '#94a3b8' }}>
              Upload untrusted media (JPEG, PNG, MP4 up to 25 MB) for safe cryptographic ingestion and container inspection.
            </p>
          </div>

          <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div
              style={{
                border: '2px dashed #475569',
                borderRadius: '0.5rem',
                padding: '1.5rem',
                textAlign: 'center',
                backgroundColor: '#0f172a',
              }}
            >
              <input
                type="file"
                id="mediaFileInput"
                accept=".jpg,.jpeg,.png,.mp4"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <label
                htmlFor="mediaFileInput"
                style={{
                  cursor: 'pointer',
                  display: 'inline-block',
                  padding: '0.5rem 1.25rem',
                  backgroundColor: '#334155',
                  borderRadius: '0.375rem',
                  color: '#f8fafc',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  marginBottom: '0.5rem',
                }}
              >
                Choose File
              </label>
              <div style={{ fontSize: '0.85rem', color: selectedFile ? '#38bdf8' : '#94a3b8' }}>
                {selectedFile ? `${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)` : 'Supported formats: JPEG, PNG, MP4'}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <button
                type="submit"
                disabled={uploadLoading || !selectedFile}
                style={{
                  backgroundColor: uploadLoading || !selectedFile ? '#475569' : '#2563eb',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '0.375rem',
                  padding: '0.6rem 1.25rem',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  cursor: uploadLoading || !selectedFile ? 'not-allowed' : 'pointer',
                  transition: 'background-color 0.2s',
                }}
              >
                {uploadLoading ? 'Ingesting...' : 'Ingest Media'}
              </button>

              {uploadError && (
                <span style={{ color: '#fca5a5', fontSize: '0.85rem' }}>
                  {uploadError}
                </span>
              )}
            </div>
          </form>

          {/* Ingestion Result Display */}
          {ingestionResult && (
            <div
              style={{
                marginTop: '1.5rem',
                padding: '1.25rem',
                backgroundColor: '#0f172a',
                borderRadius: '0.5rem',
                border: '1px solid #334155',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <span
                  style={{
                    display: 'inline-block',
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    backgroundColor: '#22c55e',
                  }}
                />
                <span style={{ fontSize: '1rem', fontWeight: 700, color: '#4ade80' }}>
                  Media successfully ingested
                </span>
                {ingestionResult.is_duplicate && (
                  <span
                    style={{
                      fontSize: '0.75rem',
                      padding: '0.15rem 0.5rem',
                      borderRadius: '9999px',
                      backgroundColor: '#3b82f6',
                      color: '#ffffff',
                      fontWeight: 600,
                      marginLeft: '0.5rem',
                    }}
                  >
                    Deduplicated (Existing Record)
                  </span>
                )}
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                  gap: '0.75rem',
                  fontSize: '0.85rem',
                  marginBottom: '1rem',
                }}
              >
                <div>
                  <span style={{ color: '#94a3b8' }}>Media ID: </span>
                  <code style={{ color: '#38bdf8' }}>{ingestionResult.media_id}</code>
                </div>
                <div>
                  <span style={{ color: '#94a3b8' }}>Validation Status: </span>
                  <span style={{ color: '#22c55e', fontWeight: 600 }}>{ingestionResult.validation_status}</span>
                </div>
                <div>
                  <span style={{ color: '#94a3b8' }}>Category / MIME: </span>
                  <span style={{ color: '#f8fafc' }}>{ingestionResult.media_category} ({ingestionResult.mime_type})</span>
                </div>
                <div>
                  <span style={{ color: '#94a3b8' }}>Original Size: </span>
                  <span style={{ color: '#f8fafc' }}>{ingestionResult.size_bytes.toLocaleString()} bytes</span>
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <span style={{ color: '#94a3b8' }}>SHA-256 Digest: </span>
                  <code style={{ color: '#a78bfa', wordBreak: 'break-all' }}>{ingestionResult.sha256_digest}</code>
                </div>
              </div>

              {/* Structured Neutral Observations (Section 21 & 22) */}
              {ingestionResult.analysis && (
                <div style={{ borderTop: '1px solid #1e293b', paddingTop: '1rem', marginTop: '0.75rem' }}>
                  <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem', color: '#cbd5e1' }}>
                    Structured Observations &amp; Container Metadata
                  </h4>
                  <pre
                    style={{
                      margin: 0,
                      padding: '0.75rem',
                      backgroundColor: '#020617',
                      borderRadius: '0.375rem',
                      overflowX: 'auto',
                      fontSize: '0.8rem',
                      color: '#38bdf8',
                    }}
                  >
                    {JSON.stringify(
                      {
                        container: ingestionResult.analysis.container,
                        metadata: ingestionResult.analysis.metadata,
                        evidence_count: ingestionResult.analysis.evidence.length,
                        integrity_verified: ingestionResult.analysis.integrity.verified,
                      },
                      null,
                      2
                    )}
                  </pre>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Media Record Lookup Card (Section 15) */}
        <section
          style={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '0.75rem',
            padding: '1.5rem',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.2)',
          }}
        >
          <div style={{ marginBottom: '1rem' }}>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600, color: '#f8fafc' }}>
              Media Record Retrieval
            </h2>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: '#94a3b8' }}>
              Retrieve structured ingestion and evidence records via <code>GET /api/v1/media/{'{media_id}'}</code>.
            </p>
          </div>

          <form onSubmit={handleLookup} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <input
              type="text"
              placeholder="Enter system media_id (UUID)..."
              value={lookupId}
              onChange={(e) => setLookupId(e.target.value)}
              style={{
                flex: 1,
                padding: '0.5rem 0.75rem',
                borderRadius: '0.375rem',
                border: '1px solid #475569',
                backgroundColor: '#0f172a',
                color: '#f8fafc',
                fontSize: '0.875rem',
              }}
            />
            <button
              type="submit"
              disabled={lookupLoading}
              style={{
                backgroundColor: lookupLoading ? '#475569' : '#334155',
                color: '#ffffff',
                border: '1px solid #475569',
                borderRadius: '0.375rem',
                padding: '0.5rem 1rem',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: lookupLoading ? 'not-allowed' : 'pointer',
              }}
            >
              {lookupLoading ? 'Fetching...' : 'Query Record'}
            </button>
          </form>

          {lookupError && (
            <div
              style={{
                marginTop: '1rem',
                padding: '0.5rem 0.75rem',
                backgroundColor: '#450a0a',
                border: '1px solid #991b1b',
                borderRadius: '0.375rem',
                color: '#fca5a5',
                fontSize: '0.85rem',
              }}
            >
              {lookupError}
            </div>
          )}
        </section>

        {/* System Verification (Section 13) */}
        <section
          style={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '0.75rem',
            padding: '1.5rem',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.2)',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem',
            }}
          >
            <div>
              <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600, color: '#f8fafc' }}>
                System Verification Probes
              </h2>
              <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: '#94a3b8' }}>
                Inspect backend health (<code>/api/v1/health</code>) and multi-service readiness (<code>/api/v1/ready</code>).
              </p>
            </div>

            <button
              onClick={runHealthCheck}
              disabled={healthLoading}
              style={{
                backgroundColor: healthLoading ? '#475569' : '#2563eb',
                color: '#ffffff',
                border: 'none',
                borderRadius: '0.375rem',
                padding: '0.5rem 1rem',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: healthLoading ? 'not-allowed' : 'pointer',
              }}
            >
              {healthLoading ? 'Checking...' : 'Check Health'}
            </button>
          </div>

          {healthError && (
            <div
              style={{
                marginTop: '1rem',
                padding: '0.75rem 1rem',
                backgroundColor: '#450a0a',
                border: '1px solid #991b1b',
                borderRadius: '0.375rem',
                color: '#fca5a5',
                fontSize: '0.85rem',
              }}
            >
              Connection Error: {healthError}
            </div>
          )}

          {healthStatus && (
            <div
              style={{
                marginTop: '1rem',
                padding: '1rem',
                backgroundColor: '#0f172a',
                borderRadius: '0.375rem',
                border: '1px solid #334155',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <span
                  style={{
                    display: 'inline-block',
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: healthStatus.status === 'healthy' ? '#22c55e' : '#ef4444',
                  }}
                />
                <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f8fafc' }}>
                  Liveness: {healthStatus.status.toUpperCase()}
                </span>
              </div>

              {readyStatus && (
                <div style={{ marginTop: '0.75rem', fontSize: '0.85rem' }}>
                  <div style={{ color: '#94a3b8', marginBottom: '0.25rem' }}>Infrastructure Readiness:</div>
                  <pre
                    style={{
                      margin: 0,
                      padding: '0.5rem',
                      backgroundColor: '#020617',
                      borderRadius: '0.25rem',
                      overflowX: 'auto',
                      fontSize: '0.8rem',
                      color: '#38bdf8',
                    }}
                  >
                    {JSON.stringify(readyStatus, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer
        style={{
          borderTop: '1px solid #1e293b',
          backgroundColor: '#090d16',
          padding: '1rem 2rem',
          textAlign: 'center',
          fontSize: '0.8rem',
          color: '#64748b',
        }}
      >
        ADDMAI &copy; {new Date().getFullYear()} &mdash; Production-Oriented Media Authenticity Analysis Platform
      </footer>
    </div>
  );
};

export default App;
