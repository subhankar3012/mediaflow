import React, { useState, useEffect, useRef } from 'react';
import { appConfig } from '../../config/appConfig';
import { triggerMonetagAd } from '../../utils/monetag';
import { AdsterraBanner } from './AdsterraBanner';

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
  const initialSeconds = seconds !== undefined ? seconds : (appConfig.interstitialCountdownSeconds || 5);
  const [secondsLeft, setSecondsLeft] = useState(initialSeconds);
  const completedRef = useRef(false);

  const handleComplete = () => {
    if (completedRef.current) return;
    completedRef.current = true;
    if (onReady) onReady();
    if (onProceed) onProceed();
    onClose();
  };

  useEffect(() => {
    if (!isOpen) {
      setSecondsLeft(initialSeconds);
      completedRef.current = false;
      return;
    }

    setSecondsLeft(initialSeconds);
    completedRef.current = false;

    // Trigger Monetag tag
    triggerMonetagAd();

    if (initialSeconds <= 0) {
      handleComplete();
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

  // Auto-close when timer reaches 0
  useEffect(() => {
    if (isOpen && secondsLeft === 0 && !completedRef.current) {
      const autoCloseTimeout = setTimeout(() => {
        handleComplete();
      }, 350);
      return () => clearTimeout(autoCloseTimeout);
    }
  }, [isOpen, secondsLeft]);

  if (!isOpen) return null;

  const percentComplete = Math.min(
    100,
    Math.round(((initialSeconds - secondsLeft) / initialSeconds) * 100)
  );

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="interstitial-modal-title"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(4px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
      }}
    >
      <div
        className="app-download-modal"
        style={{
          maxWidth: '460px',
          width: '100%',
          textAlign: 'center',
          position: 'relative',
          padding: '1.25rem 1.5rem',
          borderRadius: 'var(--radius-xl, 1rem)',
          backgroundColor: '#ffffff',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          overflow: 'hidden',
        }}
      >
        {/* Top Dismiss Button */}
        <button
          type="button"
          onClick={handleComplete}
          aria-label="Dismiss Modal"
          style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '6px',
            color: 'var(--slate-400, #94a3b8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '50%',
            transition: 'color 0.15s ease',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#0f172a')}
          onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        {/* 1. TOP: Title & Horizontal Loader */}
        <div style={{ marginBottom: '0.875rem', textAlign: 'left' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
            <span
              id="interstitial-modal-title"
              style={{ fontSize: '0.925rem', fontWeight: 700, color: 'var(--slate-900, #0f172a)' }}
            >
              Preparing High-Speed Download
            </span>
            <span
              className="font-mono"
              style={{
                fontSize: '0.75rem',
                color: '#2563eb',
                fontWeight: 600,
                backgroundColor: 'rgba(37, 99, 235, 0.08)',
                padding: '2px 8px',
                borderRadius: '999px',
              }}
            >
              {secondsLeft > 0 ? `${secondsLeft}s` : 'Ready'}
            </span>
          </div>

          {/* Horizontal animated loader bar */}
          <div
            style={{
              height: '7px',
              width: '100%',
              backgroundColor: '#f1f5f9',
              borderRadius: '999px',
              overflow: 'hidden',
              position: 'relative',
              boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.06)',
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${percentComplete}%`,
                background: 'linear-gradient(90deg, #2563eb, #10b981)',
                borderRadius: '999px',
                transition: 'width 0.9s cubic-bezier(0.4, 0, 0.2, 1)',
              }}
            />
          </div>

          <div style={{ fontSize: '0.75rem', color: 'var(--slate-500, #64748b)', marginTop: '0.35rem', display: 'flex', justifyContent: 'space-between' }}>
            <span>{fileName ? `Syncing "${fileName.length > 35 ? fileName.slice(0, 35) + '...' : fileName}"` : 'Extracting audio & video streams in background...'}</span>
            <span className="font-mono">{percentComplete}%</span>
          </div>
        </div>

        {/* 2. MIDDLE: Dedicated Ad Placement */}
        <div
          style={{
            margin: '0.5rem auto 0.75rem auto',
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '260px',
          }}
        >
          <AdsterraBanner slotType="rectangle" />
        </div>

        {/* 3. BOTTOM: Download Now Button & Auto-Close Timer */}
        <div>
          <button
            type="button"
            className="btn-download-primary"
            onClick={handleComplete}
            style={{
              width: '100%',
              padding: '0.85rem 1.25rem',
              fontSize: '1rem',
              fontWeight: 600,
              justifyContent: 'center',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              boxShadow: '0 4px 14px rgba(37, 99, 235, 0.35)',
              cursor: 'pointer',
            }}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <span>Download Now {secondsLeft > 0 ? `(${secondsLeft}s)` : ''}</span>
          </button>

          <p
            style={{
              margin: '0.5rem 0 0 0',
              fontSize: '0.75rem',
              color: 'var(--slate-500, #64748b)',
              fontFamily: 'var(--font-mono, monospace)',
            }}
          >
            Auto-closing in {secondsLeft}s... (processing in background)
          </p>
        </div>
      </div>
    </div>
  );
};
