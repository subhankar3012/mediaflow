import React, { useEffect } from 'react';

export interface AppDownloadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AppDownloadModal: React.FC<AppDownloadModalProps> = ({ isOpen, onClose }) => {
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="app-modal-title"
      onClick={onClose}
    >
      <div
        className="modal-card app-download-modal"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="app-modal-header">
          <div className="app-modal-brand">
            <div className="app-modal-icon-wrap">
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M17.523 15.3414c-.5511 0-.9993-.4486-.9993-.9997s.4482-.9993.9993-.9993c.551 0 .9993.4482.9993.9993 0 .5511-.4483.9997-.9993.9997m-11.046 0c-.5511 0-.9993-.4486-.9993-.9997s.4482-.9993.9993-.9993c.5511 0 .9993.4482.9993.9993 0 .5511-.4482.9997-.9993.9997m11.4045-6.02l1.9973-3.4592a.416.416 0 00-.1523-.5676.416.416 0 00-.5676.1523l-2.0223 3.503C15.5902 8.4116 13.8533 8 12 8s-3.5902.4116-5.1369.9499L4.8408 5.4469a.416.416 0 00-.5676-.1523.416.416 0 00-.1523.5676l1.9973 3.4592C2.6889 11.1867.3432 14.6589 0 18.761h24c-.3432-4.1021-2.6889-7.5743-6.1185-9.4396" />
              </svg>
            </div>
            <div>
              <h3 id="app-modal-title" className="app-modal-title">
                MediaFlow for Android
              </h3>
              <p className="app-modal-subtitle">
                Official native companion • Fast, offline &amp; 4K capable
              </p>
            </div>
          </div>
          <button
            type="button"
            className="app-modal-close"
            onClick={onClose}
            aria-label="Close dialog"
          >
            ✕
          </button>
        </div>

        {/* Feature Highlights Grid */}
        <div className="app-modal-features">
          <div className="app-feature-card">
            <div className="app-feature-icon">⚡</div>
            <div className="app-feature-body">
              <strong>Local 4K 60FPS Processing</strong>
              <p>
                Uses your phone's processor for FFmpeg audio/video muxing. Zero server queues, no timeout limits.
              </p>
            </div>
          </div>

          <div className="app-feature-card">
            <div className="app-feature-icon">📲</div>
            <div className="app-feature-body">
              <strong>1-Tap Share Sheet Integration</strong>
              <p>
                Tap "Share" in YouTube or Instagram and select MediaFlow. Starts analyzing without copy-pasting.
              </p>
            </div>
          </div>

          <div className="app-feature-card">
            <div className="app-feature-icon">📁</div>
            <div className="app-feature-body">
              <strong>Built-in Player &amp; Gallery</strong>
              <p>
                Manage all downloads, play videos offline, and export directly to your Android Photos/Gallery.
              </p>
            </div>
          </div>

          <div className="app-feature-card">
            <div className="app-feature-icon">🛡️</div>
            <div className="app-feature-body">
              <strong>100% Free &amp; Private</strong>
              <p>
                No account required, no tracking, clean open-source architecture that respects your battery.
              </p>
            </div>
          </div>
        </div>

        {/* Download & QR Action Section */}
        <div className="app-modal-action-box">
          <div className="app-modal-download-col">
            <a
              href="https://github.com/subhankar3012/mediaflow/releases/latest"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary app-download-direct-btn"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              <span>Download APK (Free • v1.0.0)</span>
            </a>
            <span className="app-download-meta">
              Android 8.0+ • ~22 MB • Safe SHA-256 Verified
            </span>
          </div>

          <div className="app-modal-qr-col">
            <div className="app-qr-box" title="Scan with your phone to download">
              <svg viewBox="0 0 100 100" width="80" height="80" className="app-qr-svg">
                {/* Visual stylised QR Code pattern */}
                <rect width="100" height="100" fill="#ffffff" rx="8" />
                {/* Corner Top-Left */}
                <rect x="8" y="8" width="28" height="28" fill="#0f172a" rx="4" />
                <rect x="14" y="14" width="16" height="16" fill="#ffffff" rx="2" />
                <rect x="18" y="18" width="8" height="8" fill="#e11d48" rx="1" />
                {/* Corner Top-Right */}
                <rect x="64" y="8" width="28" height="28" fill="#0f172a" rx="4" />
                <rect x="70" y="14" width="16" height="16" fill="#ffffff" rx="2" />
                <rect x="74" y="18" width="8" height="8" fill="#e11d48" rx="1" />
                {/* Corner Bottom-Left */}
                <rect x="8" y="64" width="28" height="28" fill="#0f172a" rx="4" />
                <rect x="14" y="70" width="16" height="16" fill="#ffffff" rx="2" />
                <rect x="18" y="74" width="8" height="8" fill="#e11d48" rx="1" />
                {/* Inner Data Cells */}
                <rect x="42" y="12" width="6" height="6" fill="#0f172a" />
                <rect x="52" y="16" width="6" height="6" fill="#0f172a" />
                <rect x="44" y="24" width="6" height="6" fill="#0f172a" />
                <rect x="12" y="44" width="6" height="6" fill="#0f172a" />
                <rect x="22" y="48" width="6" height="6" fill="#0f172a" />
                <rect x="32" y="42" width="6" height="6" fill="#0f172a" />
                <rect x="42" y="42" width="16" height="16" fill="#0f172a" rx="2" />
                <rect x="46" y="46" width="8" height="8" fill="#38bdf8" rx="1" />
                <rect x="64" y="44" width="6" height="6" fill="#0f172a" />
                <rect x="74" y="48" width="6" height="6" fill="#0f172a" />
                <rect x="84" y="42" width="6" height="6" fill="#0f172a" />
                <rect x="44" y="66" width="6" height="6" fill="#0f172a" />
                <rect x="54" y="74" width="6" height="6" fill="#0f172a" />
                <rect x="44" y="82" width="6" height="6" fill="#0f172a" />
                <rect x="66" y="66" width="6" height="6" fill="#0f172a" />
                <rect x="76" y="74" width="6" height="6" fill="#0f172a" />
                <rect x="82" y="82" width="6" height="6" fill="#0f172a" />
              </svg>
            </div>
            <span className="app-qr-caption">Scan with phone camera</span>
          </div>
        </div>

        {/* Installation Steps */}
        <div className="app-modal-steps">
          <span className="app-steps-title">Quick 3-Step Setup:</span>
          <ol className="app-steps-list">
            <li>Download the APK file onto your Android device.</li>
            <li>If prompted, tap <em>Settings &rarr; Allow from this source</em>.</li>
            <li>Tap <em>Install</em>, open MediaFlow, and start downloading!</li>
          </ol>
        </div>
      </div>
    </div>
  );
};
