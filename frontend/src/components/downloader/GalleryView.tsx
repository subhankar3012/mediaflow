import React, { useState } from 'react';
import type { GalleryItem } from '../../api/types';
import { api } from '../../api/client';

export interface GalleryViewProps {
  items: GalleryItem[];
  title?: string | null;
  uploader?: string | null;
  onDownloadZip: (selectedIndices: number[]) => void;
  onDownloadSingleVideo?: (item: GalleryItem) => void;
  disabled?: boolean;
}

export const GalleryView: React.FC<GalleryViewProps> = ({
  items,
  title,
  uploader,
  onDownloadZip,
  onDownloadSingleVideo,
  disabled = false,
}) => {
  const [selectedIndices, setSelectedIndices] = useState<number[]>(() =>
    items.map((it) => it.index)
  );

  const allSelected = selectedIndices.length === items.length;
  const noneSelected = selectedIndices.length === 0;

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelectedIndices([]);
    } else {
      setSelectedIndices(items.map((it) => it.index));
    }
  };

  const toggleItem = (index: number) => {
    if (selectedIndices.includes(index)) {
      setSelectedIndices(selectedIndices.filter((i) => i !== index));
    } else {
      setSelectedIndices([...selectedIndices, index].sort((a, b) => a - b));
    }
  };

  // 1-Click Direct Download for an individual photo item
  const handleDownloadSingleImage = (e: React.MouseEvent, item: GalleryItem) => {
    e.stopPropagation();
    const downloadUrl = item.display_url || item.thumbnail;
    if (!downloadUrl) return;

    const baseTitle = title ? title.replace(/[^a-zA-Z0-9_\-]/g, '_').substring(0, 30) : 'media';
    const safeFilename = `${baseTitle}_item_${item.index}`;
    const directUrl = `${api.getBaseUrl()}/api/thumbnail/download?url=${encodeURIComponent(
      downloadUrl
    )}&title=${encodeURIComponent(safeFilename)}&is_media=true`;

    const a = document.createElement('a');
    a.href = directUrl;
    a.setAttribute('download', '');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleDownloadBatch = () => {
    if (selectedIndices.length === 0) return;
    onDownloadZip(selectedIndices);
  };

  const photosCount = items.filter((i) => i.type === 'image').length;
  const videosCount = items.filter((i) => i.type === 'video').length;

  return (
    <div className="gallery-view-container" aria-label="Carousel Gallery Preview">
      {/* Gallery Header Info & Batch Actions */}
      <div className="gallery-header-bar">
        <div className="gallery-title-area">
          <div className="gallery-badge-row">
            <span className="gallery-pill-count">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <polyline points="21 15 16 10 5 21" />
              </svg>
              {items.length} {items.length === 1 ? 'Item' : 'Items'}
            </span>

            {photosCount > 0 && (
              <span className="gallery-meta-tag">
                {photosCount} {photosCount === 1 ? 'Photo' : 'Photos'}
              </span>
            )}
            {videosCount > 0 && (
              <span className="gallery-meta-tag">
                {videosCount} {videosCount === 1 ? 'Video' : 'Videos'}
              </span>
            )}
          </div>

          <h3 className="gallery-post-title">
            {title || 'Instagram Post'}
          </h3>
          {uploader && (
            <p className="gallery-post-uploader">
              by <strong>@{uploader}</strong>
            </p>
          )}
        </div>

        <div className="gallery-actions-toolbar">
          <button
            type="button"
            onClick={toggleSelectAll}
            className="gallery-select-all-btn"
            disabled={disabled}
            title={allSelected ? 'Deselect All' : 'Select All'}
          >
            {allSelected ? 'Deselect All' : 'Select All'}
          </button>

          <button
            type="button"
            onClick={handleDownloadBatch}
            disabled={disabled || noneSelected}
            className="btn-download-primary gallery-batch-btn"
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
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <span>
              {allSelected
                ? `Download All (${items.length} in ZIP)`
                : `Download Selected (${selectedIndices.length} in ZIP)`}
            </span>
          </button>
        </div>
      </div>

      {/* Grid of Gallery Slides */}
      <div className="gallery-grid">
        {items.map((item) => {
          const isSelected = selectedIndices.includes(item.index);
          const isVideo = item.type === 'video';

          return (
            <div
              key={item.id || item.index}
              className={`gallery-card ${isSelected ? 'selected' : ''}`}
              onClick={() => toggleItem(item.index)}
              role="checkbox"
              aria-checked={isSelected}
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === ' ' || e.key === 'Enter') {
                  e.preventDefault();
                  toggleItem(item.index);
                }
              }}
            >
              {/* Media Preview Box */}
              <div className="gallery-card-thumb-wrap">
                {item.thumbnail || item.display_url ? (
                  <img
                    src={item.thumbnail || item.display_url || ''}
                    alt={`Slide #${item.index}`}
                    className="gallery-card-img"
                    loading="lazy"
                  />
                ) : (
                  <div className="gallery-card-placeholder">
                    {isVideo ? '🎥' : '📷'}
                  </div>
                )}

                {/* Index / Type Badge Overlay */}
                <div className="gallery-card-badges">
                  <span className="gallery-item-index-badge">#{item.index}</span>
                  <span className={`gallery-item-type-badge ${isVideo ? 'video' : 'photo'}`}>
                    {isVideo ? 'Video' : 'Photo'}
                  </span>
                </div>

                {/* Selection Checkbox Pill */}
                <div
                  className={`gallery-card-checkbox ${isSelected ? 'checked' : ''}`}
                  aria-hidden="true"
                >
                  {isSelected && (
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  )}
                </div>
              </div>

              {/* Card Footer with Quick Download CTA */}
              <div className="gallery-card-footer">
                <span className="gallery-card-caption">
                  {isVideo ? 'MP4 Video' : 'HD Image'}
                </span>

                <button
                  type="button"
                  onClick={(e) => {
                    if (isVideo && onDownloadSingleVideo) {
                      e.stopPropagation();
                      onDownloadSingleVideo(item);
                    } else {
                      handleDownloadSingleImage(e, item);
                    }
                  }}
                  className="gallery-item-download-btn"
                  title={`Download Slide #${item.index}`}
                  aria-label={`Download item ${item.index}`}
                  disabled={disabled}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  <span>Download</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
