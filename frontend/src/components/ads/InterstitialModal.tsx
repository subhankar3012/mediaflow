import React, { useState, useEffect } from 'react';
import { appConfig } from '../../config/appConfig';

export interface InterstitialModalProps {
  isOpen: boolean;
  onProceed?: () => void;
  onReady?: () => void;
  onClose: () => void;
  seconds?: number;
  fileName?: string;
}

export const InterstitialModal: React.FC<InterstitialModalProps> = ({
  isOpen,
  onProceed,
  onReady,
  onClose,
  seconds,
  fileName,
}) => {
  const initialSeconds = seconds !== undefined ? seconds : appConfig.interstitialCountdownSeconds;
  const [secondsLeft, setSecondsLeft] = useState(initialSeconds);

  const handleComplete = () => {
    if (onReady) onReady();
    if (onProceed) onProceed();
  };

  useEffect(() => {
    if (!isOpen) {
      setSecondsLeft(initialSeconds);
      return;
    }

    const timer = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isOpen, initialSeconds]);

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div className="modal-card">
        <h3 id="modal-title" className="section-h2" style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>
          Preparing Your Download
        </h3>
        <p className="hero-subtitle" style={{ fontSize: '0.9rem' }}>
          {fileName ? `Preparing "${fileName}"...` : 'Connecting to the high-speed download engine...'}
        </p>

        <div
          style={{
            minHeight: '200px',
            margin: '1.5rem 0',
            background: 'var(--bg-tertiary)',
            borderRadius: 'var(--radius-md)',
            border: '1px dashed var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1rem',
          }}
        >
          <span className="ad-label">Advertisement</span>
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            Sponsored Placement
          </span>
        </div>

        <p className="modal-countdown">
          {secondsLeft > 0 ? (
            <>Your file will be ready in <strong>{secondsLeft}s</strong>...</>
          ) : (
            <>Your download stream is ready!</>
          )}
        </p>

        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
          <button
            type="button"
            className="btn-primary"
            onClick={handleComplete}
            disabled={secondsLeft > 0}
            style={{ minWidth: '160px' }}
          >
            Continue
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={onClose}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};
