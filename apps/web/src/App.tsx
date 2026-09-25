import React, { useState } from 'react';
import apiService from './services/api';
import { HealthResponse, ReadyResponse } from './types';

export const App: React.FC = () => {
  const [healthStatus, setHealthStatus] = useState<HealthResponse | null>(null);
  const [readyStatus, setReadyStatus] = useState<ReadyResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const runHealthCheck = async () => {
    setLoading(true);
    setError(null);
    try {
      const [health, ready] = await Promise.all([
        apiService.checkHealth(),
        apiService.checkReadiness(),
      ]);
      setHealthStatus(health);
      setReadyStatus(ready);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Unable to connect to backend API');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header
        style={{
          borderBottom: '1px solid #1e293b',
          backgroundColor: '#090d16',
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
              Stage 1: Infrastructure
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

      {/* Main Content Shell */}
      <main
        style={{
          flex: 1,
          maxWidth: '1000px',
          width: '100%',
          margin: '0 auto',
          padding: '2.5rem 1.5rem',
        }}
      >
        {/* Notice Banner */}
        <div
          style={{
            backgroundColor: '#1e1b4b',
            border: '1px solid #4338ca',
            borderRadius: '0.5rem',
            padding: '1rem 1.25rem',
            marginBottom: '2rem',
            color: '#c7d2fe',
            fontSize: '0.9rem',
          }}
        >
          <strong>Stage 1 Status:</strong> Core Repository &amp; Development Infrastructure.
          Deepfake models, video/audio extraction, and forensic pipelines will be introduced in subsequent stages.
        </div>

        {/* System Health Card */}
        <section
          style={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '0.75rem',
            padding: '1.5rem',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
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
                System Verification
              </h2>
              <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: '#94a3b8' }}>
                Probe backend liveness (<code>/api/v1/health</code>) and readiness (<code>/api/v1/ready</code>).
              </p>
            </div>

            <button
              onClick={runHealthCheck}
              disabled={loading}
              style={{
                backgroundColor: loading ? '#475569' : '#2563eb',
                color: '#ffffff',
                border: 'none',
                borderRadius: '0.375rem',
                padding: '0.5rem 1rem',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'background-color 0.2s',
              }}
            >
              {loading ? 'Checking...' : 'Check Health'}
            </button>
          </div>

          {error && (
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
              Connection Error: {error}
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

        {/* Stack Overview */}
        <section style={{ marginTop: '2rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#94a3b8', marginBottom: '1rem' }}>
            Infrastructure Stack Services
          </h3>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem',
            }}
          >
            {[
              { name: 'FastAPI Gateway', port: '8000', desc: 'REST API, Health probes' },
              { name: 'React Frontend', port: '5173', desc: 'Web Dashboard shell' },
              { name: 'PostgreSQL 16', port: '5432', desc: 'Metadata & audit persistence' },
              { name: 'Redis 7', port: '6379', desc: 'Task broker & state cache' },
              { name: 'MinIO Storage', port: '9000/9001', desc: 'S3-compatible object store' },
            ].map((svc) => (
              <div
                key={svc.name}
                style={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '0.5rem',
                  padding: '1rem',
                }}
              >
                <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#f1f5f9' }}>{svc.name}</div>
                <div style={{ fontSize: '0.75rem', color: '#38bdf8', marginTop: '0.2rem' }}>Port: {svc.port}</div>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.4rem' }}>{svc.desc}</div>
              </div>
            ))}
          </div>
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
        ADDMAI &copy; {new Date().getFullYear()} — Production-Oriented Media Authenticity Analysis Platform
      </footer>
    </div>
  );
};

export default App;
