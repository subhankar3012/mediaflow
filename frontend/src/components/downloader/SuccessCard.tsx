import React from 'react';
import { AdSlot } from '../ads/AdSlot';
import { appConfig } from '../../config/appConfig';

export interface SuccessCardProps {
  title?: string | null;
  thumbnail?: string | null;
  fileSize?: number | null;
  outputFormat: 'mp4' | 'mp3' | 'thumbnail' | 'zip' | string;
  downloadUrl: string;
  isInstagram?: boolean;
  onReset: () => void;
}

function formatBytes(bytes?: number | null): string {
  if (!bytes || bytes <= 0) return '';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

export const SuccessCard: React.FC<SuccessCardProps> = ({
  title,
  thumbnail,
  fileSize,
  outputFormat,
  downloadUrl,
  isInstagram = false,
  onReset,
}) => {
  const [downloadTriggered, setDownloadTriggered] = React.useState(false);
  const autoTriggeredRef = React.useRef(false);

  const handleDownload = () => {
    if (!downloadUrl) return;
    setDownloadTriggered(true);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.setAttribute('download', '');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  // Automatic download initiation: slides to result and starts downloading immediately!
  React.useEffect(() => {
    if (downloadUrl && !autoTriggeredRef.current) {
      autoTriggeredRef.current = true;
      const timer = window.setTimeout(() => {
        handleDownload();
      }, 550);
      return () => clearTimeout(timer);
    }
  }, [downloadUrl]);

  const badgeText = outputFormat.toUpperCase();
  const sizeText = formatBytes(fileSize);

  const headingText =
    outputFormat === 'zip'
      ? 'Your ZIP package is ready'
      : isInstagram
      ? 'Your media is ready'
      : 'Your download is ready';

  const downloadButtonText =
    outputFormat === 'zip'
      ? 'Download ZIP Archive'
      : outputFormat === 'mp3'
      ? 'Download MP3'
      : outputFormat === 'thumbnail'
      ? 'Download Cover Art'
      : outputFormat === 'jpg'
      ? 'Download Photo'
      : 'Download Video';

  return (
    <div className="editorial-success-card" role="status" aria-live="polite">
      {/* Green Check Icon Pill */}
      <div className="success-badge-row">
        <span className="success-pill-tag">
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="20 6 9 17 4 12" />
          </svg>
          Direct Stream Generated
        </span>
      </div>

      <h3 className="success-heading">{headingText}</h3>

      {thumbnail && (
        <div className="success-thumb-wrapper">
          <img
            src={thumbnail}
            alt={title || 'Converted media'}
            className="success-thumb-img"
          />
        </div>
      )}

      <p className="success-meta-desc">
        {title ? `"${title}"` : 'Stream verified and prepared.'}{' '}
        {badgeText && <span className="success-format-pill">{badgeText}</span>}
        {sizeText && <span className="success-size-label">({sizeText})</span>}
      </p>

      {/* Auto-download notification notice */}
      {downloadTriggered && (
        <div className="success-autodownload-notice" role="status">
          <span className="autodownload-pulse-dot" />
          <span>Download started automatically! If it didn't save, tap the button below.</span>
        </div>
      )}

      {/* CTA Buttons */}
      <div className="success-cta-row">
        <button
          type="button"
          onClick={handleDownload}
          className="btn-download-primary"
          aria-label="Download your converted media file"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          <span>{downloadButtonText}</span>
        </button>

        <button
          type="button"
          onClick={() => {
            const directLink = appConfig.monetagDirectLink || appConfig.adsterraDirectLink;
            if (appConfig.enableAds && directLink) {
              try {
                window.open(directLink, '_blank', 'noopener,noreferrer');
              } catch {}
            }
            onReset();
          }}
          className="btn-search-secondary"
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <polyline points="1 4 1 10 7 10" />
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
          </svg>
          <span>Search Another</span>
        </button>
      </div>

      {/* Sponsored Banner on Completed Screen */}
      <div style={{ marginTop: '1.25rem', width: '100%', display: 'flex', justifyContent: 'center' }}>
        <AdSlot slotId="ad-success-banner" slotType="banner468" label="Sponsored Placement" />
      </div>
    </div>
  );
};
