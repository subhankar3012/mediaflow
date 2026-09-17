import React from 'react';
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
  onCancel?: () => void;
}

export const ProgressCard: React.FC<ProgressCardProps> = ({
  job,
  progress,
  status,
  isInstagram = false,
  onCancel,
}) => {
  const currentProgress = progress !== undefined ? progress : job?.progress || 0;
  const rawStatus = (status || job?.status || 'PROCESSING').toUpperCase();
  const pct = Math.min(Math.max(currentProgress, 0), 100);

  // Map backend states to consumer-friendly status labels
  let statusLabel: string;
  let isIndeterminate = false;

  if (rawStatus === 'QUEUED') {
    statusLabel = 'Waiting to start...';
  } else if (rawStatus === 'MERGING') {
    statusLabel = 'Processing your file...';
    isIndeterminate = true;
  } else if (rawStatus === 'TRANSCODING') {
    statusLabel = 'Optimizing your file...';
    isIndeterminate = true;
  } else if (rawStatus === 'VALIDATING') {
    statusLabel = 'Checking your file...';
    isIndeterminate = true;
  } else if (rawStatus === 'COMPLETED') {
    statusLabel = isInstagram ? 'Your video is ready' : 'Your download is ready';
  } else if (rawStatus === 'FAILED') {
    statusLabel = 'Something went wrong';
  } else if (rawStatus === 'EXPIRED') {
    statusLabel = 'This download has expired';
  } else {
    // PROCESSING or DOWNLOADING
    if (pct >= 100) {
      statusLabel = 'Processing your file...';
      isIndeterminate = true;
    } else {
      statusLabel = isInstagram ? 'Preparing your video...' : 'Preparing your download...';
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
          {statusLabel}
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
        <p>This may take a moment while our worker processes and validates the media stream.</p>
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
