import React, { useState, useEffect } from 'react';
import type { JobResponse, SSEEventData, JobStatus } from '../../api/types';

export interface ProgressCardProps {
  job?: JobResponse | SSEEventData;
  progress?: number;
  status?: JobStatus;
  speed?: string | null;
  eta?: string | null;
  downloadedBytes?: number | null;
  totalBytes?: number | null;
  isInstagram?: boolean;
  outputFormat?: string;
  onCancel?: () => void;
}

const VIDEO_STEPS = [
  'Connecting to high-speed stream...',
  'Fetching best quality audio & video...',
  'Processing media streams...',
  'Optimizing file for smooth playback...',
  'Almost done, putting everything together...',
  'Very close now, preparing your file...',
  'Finalizing, just a moment...',
];

const GALLERY_STEPS = [
  'Connecting to media gallery...',
  'Downloading high-resolution items...',
  'Compressing into clean ZIP package...',
  'Almost done, validating archive files...',
  'Very close now, preparing your download...',
  'Finalizing ZIP package, just a moment...',
];

const REASSURING_HINTS = [
  'Hang tight! Fetching the highest available quality for you.',
  'Almost done! Processing media streams seamlessly.',
  'Wait a moment — optimizing for high-speed delivery.',
  'Very close now! Assembling the file safely for your device.',
  'Just a few moments remaining...',
];

export const ProgressCard: React.FC<ProgressCardProps> = ({
  job,
  progress,
  status,
  isInstagram = false,
  outputFormat,
  onCancel,
}) => {
  const currentProgress = progress !== undefined ? progress : job?.progress || 0;
  const rawStatus = (status || job?.status || 'PROCESSING').toUpperCase();
  const pct = Math.min(Math.max(currentProgress, 0), 100);

  const steps = outputFormat === 'zip' ? GALLERY_STEPS : VIDEO_STEPS;
  const [stepIndex, setStepIndex] = useState(0);
  const [hintIndex, setHintIndex] = useState(0);

  // Smoothly cycle through progressive status lines every 2.8 seconds
  useEffect(() => {
    if (['COMPLETED', 'FAILED', 'EXPIRED'].includes(rawStatus)) return;

    const timer = window.setInterval(() => {
      setStepIndex((prev) => (prev + 1) % steps.length);
      setHintIndex((prev) => (prev + 1) % REASSURING_HINTS.length);
    }, 2800);

    return () => clearInterval(timer);
  }, [rawStatus, steps.length]);

  // Map backend states to consumer-friendly status labels
  let statusLabel: string;
  let isIndeterminate = false;

  if (rawStatus === 'QUEUED') {
    statusLabel = 'Waiting to start...';
  } else if (rawStatus === 'MERGING' || rawStatus === 'TRANSCODING') {
    statusLabel = pct >= 90 ? 'Very close now, finalizing your file...' : steps[stepIndex];
    isIndeterminate = true;
  } else if (rawStatus === 'VALIDATING') {
    statusLabel = 'Checking file integrity...';
    isIndeterminate = true;
  } else if (rawStatus === 'COMPLETED') {
    statusLabel = outputFormat === 'zip'
      ? 'Your ZIP package is ready'
      : isInstagram
      ? 'Your media is ready'
      : 'Your download is ready';
  } else if (rawStatus === 'FAILED') {
    statusLabel = 'Something went wrong';
  } else if (rawStatus === 'EXPIRED') {
    statusLabel = 'This download has expired';
  } else {
    // PROCESSING or DOWNLOADING
    if (pct >= 90) {
      statusLabel = outputFormat === 'zip' ? 'Almost done, packaging ZIP file...' : 'Very close now, finalizing your file...';
      isIndeterminate = true;
    } else {
      statusLabel = steps[stepIndex];
    }
  }

  return (
    <div
      className="editorial-progress-card"
      role="region"
      aria-label="Download Preparation Progress"
      aria-live="polite"
    >
      <div className="progress-status-row">
        <span className="progress-status-title">
          <svg className="spinner" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
            <path d="M12 2a10 10 0 0 1 10 10" />
          </svg>
          <span className="progress-dynamic-label">{statusLabel}</span>
        </span>
        {!isIndeterminate && pct > 0 && pct < 100 && (
          <span className="progress-pct-badge font-mono">
            {pct.toFixed(0)}%
          </span>
        )}
      </div>

      {/* Progress Track */}
      <div className="progress-track" aria-hidden="true">
        {isIndeterminate ? (
          <div className="progress-fill indeterminate" />
        ) : (
          <div className="progress-fill" style={{ width: `${pct}%` }} />
        )}
      </div>

      <div className="progress-support-note">
        <div className="progress-ticker-badge">
          <span className="progress-ticker-dot" />
          <span className="progress-ticker-text">{REASSURING_HINTS[hintIndex]}</span>
        </div>
        <span className="progress-note-sub">Please keep this tab open until your file is ready.</span>
      </div>

      {onCancel && (
        <div style={{ marginTop: 'var(--space-2)', textAlign: 'right' }}>
          <button
            type="button"
            onClick={onCancel}
            className="progress-cancel-btn"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
};
