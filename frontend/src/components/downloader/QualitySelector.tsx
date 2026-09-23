import React from 'react';
import type { NormalizedFormat, OutputType } from '../../api/types';

export interface QualitySelectorProps {
  outputType: OutputType;
  formats: NormalizedFormat[];
  selectedFormatId: string;
  onSelectFormatId?: (formatId: string) => void;
  onChange?: (formatId: string) => void;
  disabled?: boolean;
}

function formatBytes(bytes?: number | null): string {
  if (!bytes || bytes <= 0) return '';
  const mb = bytes / (1024 * 1024);
  if (mb >= 1000) {
    return `${(mb / 1024).toFixed(1)} GB`;
  }
  return `${Math.round(mb)} MB`;
}

function getSubLabel(height?: number | null, outputType?: OutputType): string {
  if (outputType === 'mp3') return 'HQ Audio Only';
  if (!height) return 'Standard Video';
  if (height >= 2160) return '4K Ultra HD';
  if (height >= 1440) return '2K Quad HD';
  if (height >= 1080) return 'Full HD MP4';
  if (height >= 720) return 'Standard HD';
  if (height >= 480) return 'Fast SD Save';
  if (height >= 360) return 'Mobile Data';
  return 'Low Bitrate';
}

function getDisplayResolution(f: NormalizedFormat, outputType: OutputType): string {
  if (outputType === 'mp3') return '320kbps';
  if (f.height) return `${f.height}p`;
  return f.quality || 'Auto';
}

export const QualitySelector: React.FC<QualitySelectorProps> = ({
  outputType,
  formats,
  selectedFormatId,
  onSelectFormatId,
  onChange,
  disabled = false,
}) => {
  // Thumbnails do not show quality selector
  if (outputType === 'thumbnail') {
    return null;
  }

  // Filter formats based on outputType
  const relevantFormats = formats.filter((f) => {
    if (outputType === 'mp3') {
      return f.has_audio && !f.has_video;
    }
    return f.has_video;
  });

  const handlePick = (formatId: string) => {
    if (disabled) return;
    if (onSelectFormatId) onSelectFormatId(formatId);
    if (onChange) onChange(formatId);
  };

  const selectedFormat = relevantFormats.find((f) => f.format_id === selectedFormatId);
  const isHighRes = selectedFormat && selectedFormat.height && selectedFormat.height >= 1440;

  return (
    <div className="quality-editorial-container">
      <div className="quality-header-row">
        <span className="quality-header-title">
          Select {outputType === 'mp3' ? 'Audio Bitrate' : 'Resolution'}
        </span>
        <span className="quality-header-hint">Audio Sync Guaranteed</span>
      </div>

      {relevantFormats.length === 0 ? (
        <p className="quality-empty-hint">Best available default selected</p>
      ) : (
        <>
          <div
            className="quality-cards-grid"
            role="radiogroup"
            aria-label="Resolution options"
          >
            {relevantFormats.map((f) => {
              const isSelected = selectedFormatId === f.format_id;
              const sizeStr = formatBytes(f.filesize_approx || f.filesize);
              const resLabel = getDisplayResolution(f, outputType);
              const subLabel = getSubLabel(f.height, outputType);
              const is4KOr2K = f.height && f.height >= 1440;

              return (
                <button
                  key={f.format_id}
                  type="button"
                  role="radio"
                  aria-checked={isSelected}
                  className={`quality-editorial-card ${isSelected ? 'active' : ''}`}
                  onClick={() => handlePick(f.format_id)}
                  disabled={disabled}
                >
                  <div className="quality-card-top">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <span className="quality-res-title">{resLabel}</span>
                      {is4KOr2K && <span className="quality-app-badge">⚡ App Recommended</span>}
                    </div>
                    <span className={`quality-check-dot ${isSelected ? 'checked' : ''}`} />
                  </div>
                  <div className="quality-sub-desc">{subLabel}</div>
                  {sizeStr && <div className="quality-size-badge">{sizeStr}</div>}
                </button>
              );
            })}
          </div>

          {/* Smart In-Context Nudge for 4K / 2K resolutions */}
          {isHighRes && (
            <div className="quality-app-tip-banner">
              <div className="quality-app-tip-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d="M17.523 15.3414c-.5511 0-.9993-.4486-.9993-.9997s.4482-.9993.9993-.9993c.551 0 .9993.4482.9993.9993 0 .5511-.4483.9997-.9993.9997m-11.046 0c-.5511 0-.9993-.4486-.9993-.9997s.4482-.9993.9993-.9993c.5511 0 .9993.4482.9993.9993 0 .5511-.4482.9997-.9993.9997m11.4045-6.02l1.9973-3.4592a.416.416 0 00-.1523-.5676.416.416 0 00-.5676.1523l-2.0223 3.503C15.5902 8.4116 13.8533 8 12 8s-3.5902.4116-5.1369.9499L4.8408 5.4469a.416.416 0 00-.5676-.1523.416.416 0 00-.1523.5676l1.9973 3.4592C2.6889 11.1867.3432 14.6589 0 18.761h24c-.3432-4.1021-2.6889-7.5743-6.1185-9.4396" />
                </svg>
              </div>
              <div className="quality-app-tip-text">
                <strong>Looking for smooth {selectedFormat?.height && selectedFormat.height >= 2160 ? '4K 60FPS' : '2K Quad HD'}?</strong>
                <span>Large 4K streams can be slow in browsers. For local hardware-accelerated processing with 0 server queue, get the free <strong>MediaFlow Android App</strong>.</span>
              </div>
              <button
                type="button"
                className="quality-app-tip-btn"
                onClick={() => window.dispatchEvent(new CustomEvent('mediaflow:open-app-modal'))}
              >
                Get Free APK
              </button>
            </div>
          )}
        </>
      )}
    </div>

  );
};
