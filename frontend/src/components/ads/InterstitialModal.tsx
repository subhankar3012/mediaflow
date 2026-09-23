import React, { useState, useEffect, useRef } from 'react';
import { appConfig } from '../../config/appConfig';
import { triggerMonetagAd } from '../../utils/monetag';

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
  const completedRef = useRef(false);

  const handleComplete = () => {
    if (completedRef.current) return;
    completedRef.current = true;
    if (onReady) onReady();
    if (onProceed) onProceed();
  };

  useEffect(() => {
    if (!isOpen) {
      setSecondsLeft(initialSeconds);
      completedRef.current = false;
      return;
    }

    // Trigger Monetag Ad dynamically during download processing time
    triggerMonetagAd();

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

  // Auto-proceed when countdown finishes
  useEffect(() => {
    if (isOpen && secondsLeft === 0 && !completedRef.current) {
      const autoProceedTimeout = setTimeout(() => {
        handleComplete();
      }, 350);
      return () => clearTimeout(autoProceedTimeout);
    }
  }, [isOpen, secondsLeft]);

  if (!isOpen) return null;

  const percentComplete = Math.min(
    100,
    Math.round(((initialSeconds - secondsLeft) / initialSeconds) * 100)
  );

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div className="app-download-modal" style={{ maxWidth: '480px', textAlign: 'center' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, rgba(37,99,235,0.12), rgba(16,185,129,0.12))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--brand-primary, #2563eb)',
            }}
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
          </div>
        </div>

        <h3 id="modal-title" style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 0.5rem', color: 'var(--slate-900)' }}>
          Preparing High-Speed Download
        </h3>
        <p style={{ fontSize: '0.875rem', color: 'var(--slate-600)', margin: '0 0 1.25rem', lineHeight: 1.5 }}>
          {fileName ? `Encoding & syncing "${fileName.length > 50 ? fileName.slice(0, 50) + '...' : fileName}"` : 'Allocating high-speed audio & video stream...'}
        </p>

        {/* Animated Progress Bar */}
        <div style={{ margin: '1rem 0 1.25rem' }}>
          <div
            style={{
              height: '8px',
              width: '100%',
              backgroundColor: 'var(--slate-100, #f1f5f9)',
              borderRadius: '999px',
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${percentComplete}%`,
                background: 'linear-gradient(90deg, #2563eb, #10b981)',
                borderRadius: '999px',
                transition: 'width 0.8s ease-in-out',
              }}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--slate-500)', marginTop: '0.4rem', fontFamily: 'var(--font-mono)' }}>
            <span>Synchronizing stream</span>
            <span>{secondsLeft > 0 ? `${secondsLeft}s remaining` : 'Ready!'}</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', marginTop: '1.25rem' }}>
          <button
            type="button"
            className="btn-download-primary"
            onClick={handleComplete}
            style={{ flex: 1, padding: '0.75rem 1rem', fontSize: '0.95rem', justifyContent: 'center' }}
          >
            {secondsLeft > 0 ? `Start Download Now (${secondsLeft}s)` : 'Download Starting...'}
          </button>
          <button
            type="button"
            onClick={onClose}
            style={{
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--slate-200)',
              backgroundColor: '#ffffff',
              color: 'var(--slate-700)',
              fontWeight: 500,
              fontSize: '0.875rem',
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};
