import React from 'react';
import type { AnalyzeResponse } from '../../api/types';

export interface MediaPreviewProps {
  media?: AnalyzeResponse;
  title?: string | null;
  thumbnail?: string | null;
  duration?: number | null;
  author?: string | null;
  platform?: string;
}

function formatDuration(seconds?: number | null): string {
  if (!seconds || seconds <= 0) return '';
  const totalSecs = Math.floor(seconds);
  const hrs = Math.floor(totalSecs / 3600);
  const mins = Math.floor((totalSecs % 3600) / 60);
  const secs = totalSecs % 60;

  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export const MediaPreview: React.FC<MediaPreviewProps> = ({
  media,
  title,
  thumbnail,
  duration,
  author,
  platform,
}) => {
  const displayTitle = title || media?.title || 'Untitled Media';
  const displayThumbnail = thumbnail || media?.thumbnail;
  const displayDuration = duration !== undefined ? duration : media?.duration;
  const displayAuthor = author || media?.uploader;
  const displayPlatform = platform || media?.platform || 'Video';

  const durationStr = formatDuration(displayDuration);

  return (
    <div className="preview-editorial-header" aria-label="Media Preview">
      {/* 16:9 Thumbnail Frame */}
      <div className="preview-thumb-frame">
        {displayThumbnail ? (
          <img
            src={displayThumbnail}
            alt={displayTitle}
            className="preview-thumb-img"
            loading="lazy"
          />
        ) : (
          <div className="preview-thumb-fallback">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="6 4 20 12 6 20 6 4" />
            </svg>
          </div>
        )}
        {durationStr && <span className="preview-duration-badge">{durationStr}</span>}
        <span className="preview-hd-badge">HD</span>
      </div>

      {/* Media Details */}
      <div className="preview-info-col">
        <div className="preview-meta-row">
          <span className="preview-platform-label">{displayPlatform} Stream</span>
          <span className="meta-sep">•</span>
          <span className="preview-verified-badge">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            Verified Stream
          </span>
        </div>

        <h2 className="preview-title" title={displayTitle}>
          {displayTitle}
        </h2>

        {displayAuthor && (
          <p className="preview-author-text">
            Channel: <strong>{displayAuthor}</strong>
          </p>
        )}
      </div>
    </div>
  );
};
