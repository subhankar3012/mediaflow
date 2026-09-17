import React from 'react';
import { Link } from '../../router/Link';

export interface ToolItem {
  path: string;
  name: string;
  category: string;
  description: string;
}

const TOOLS_LIST: ToolItem[] = [
  {
    path: '/youtube-video-downloader',
    name: 'YouTube Video Downloader',
    category: 'YOUTUBE',
    description: 'Full HD 1080p & 720p MP4 with full audio track sync.',
  },
  {
    path: '/youtube-to-mp3',
    name: 'YouTube to MP3 Converter',
    category: 'AUDIO EXTRACTION',
    description: 'Lossless 320kbps audio bitrate for podcasts & music.',
  },
  {
    path: '/youtube-to-mp4',
    name: 'YouTube to MP4 Downloader',
    category: 'ULTRA HD',
    description: 'High-speed conversion to universally compatible MP4.',
  },
  {
    path: '/instagram-downloader',
    name: 'Instagram Video Downloader',
    category: 'INSTAGRAM',
    description: 'Direct CDN extraction for feed clips and carousel items.',
  },
  {
    path: '/instagram-reels-downloader',
    name: 'Instagram Reels Downloader',
    category: 'VERTICAL VIDEO',
    description: 'Vertical 9:16 high-definition video with original audio.',
  },
];

export interface RelatedToolsProps {
  currentPath?: string;
}

export const RelatedTools: React.FC<RelatedToolsProps> = ({ currentPath = '/' }) => {
  const filtered = TOOLS_LIST.filter((t) => t.path !== currentPath);

  return (
    <section className="related-tools-section" aria-labelledby="related-tools-heading">
      <div className="site-container">
        {/* Section Header */}
        <div className="related-tools-header">
          <div>
            <h3 id="related-tools-heading" className="related-header-title">
              Dedicated Specialized Tools
            </h3>
            <p className="related-header-subtitle">
              High-speed transcoder endpoints tuned for specific formats.
            </p>
          </div>
          <span className="related-count-tag font-mono">
            {filtered.length} Active Tools
          </span>
        </div>

        {/* 3-Column Compact Card Grid */}
        <div className="related-compact-grid">
          {filtered.map((tool) => (
            <Link
              key={tool.path}
              to={tool.path}
              className="related-compact-card group"
            >
              <div className="card-category-row font-mono">
                <span>{tool.category}</span>
                <svg
                  className="card-arrow-icon"
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </div>
              <h4 className="card-tool-name">{tool.name}</h4>
              <p className="card-tool-desc">{tool.description}</p>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
};
