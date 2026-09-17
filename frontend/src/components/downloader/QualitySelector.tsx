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
                  <span className="quality-res-title">{resLabel}</span>
                  <span className={`quality-check-dot ${isSelected ? 'checked' : ''}`} />
                </div>
                <div className="quality-sub-desc">{subLabel}</div>
                {sizeStr && <div className="quality-size-badge">{sizeStr}</div>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
