import React from 'react';

export const SkeletonCard: React.FC = () => {
  return (
    <div
      className="downloader-result-card skeleton-card"
      aria-busy="true"
      aria-label="Loading media details"
    >
      {/* Header matching MediaPreview layout */}
      <div className="preview-editorial-header skeleton-header">
        {/* 16:9 Thumbnail Skeleton */}
        <div className="skeleton-thumb-frame skeleton-shimmer" />

        {/* Media Details Skeleton */}
        <div className="preview-info-col skeleton-info-col">
          {/* Platform badge pill */}
          <div className="skeleton-line skeleton-badge skeleton-shimmer" />

          {/* 2-line title skeleton */}
          <div className="skeleton-line skeleton-title-1 skeleton-shimmer" />
          <div className="skeleton-line skeleton-title-2 skeleton-shimmer" />

          {/* Author line */}
          <div className="skeleton-line skeleton-author skeleton-shimmer" />
        </div>
      </div>

      {/* Tabs placeholder */}
      <div className="skeleton-tabs-row">
        <div className="skeleton-tab skeleton-shimmer" />
        <div className="skeleton-tab skeleton-shimmer" />
        <div className="skeleton-tab skeleton-shimmer" />
      </div>

      {/* Quality dropdown placeholder */}
      <div className="skeleton-dropdown skeleton-shimmer" />

      {/* Primary Action Button skeleton */}
      <div className="skeleton-cta-btn skeleton-shimmer" />

      {/* Reassuring loading note */}
      <div className="skeleton-status-hint">
        <span className="skeleton-spinner-dot" />
        <span>Analyzing media & fetching highest available quality...</span>
      </div>
    </div>
  );
};
