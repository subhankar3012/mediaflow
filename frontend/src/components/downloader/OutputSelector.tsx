import React from 'react';

export type OutputType = 'mp4' | 'mp3' | 'thumbnail';

export interface OutputSelectorProps {
  selected: OutputType;
  onSelect?: (type: OutputType) => void;
  onChange?: (type: OutputType) => void;
  disabled?: boolean;
}

export const OutputSelector: React.FC<OutputSelectorProps> = ({
  selected,
  onSelect,
  onChange,
  disabled = false,
}) => {
  const handleSelect = (type: OutputType) => {
    if (onSelect) onSelect(type);
    if (onChange) onChange(type);
  };

  return (
    <div
      className="editorial-output-tabs"
      role="tablist"
      aria-label="Select download output format"
    >
      <button
        type="button"
        role="tab"
        aria-selected={selected === 'mp4'}
        className={`editorial-tab-btn ${selected === 'mp4' ? 'active' : ''}`}
        onClick={() => handleSelect('mp4')}
        disabled={disabled}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="23 7 16 12 23 17 23 7" />
          <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
        </svg>
        <span>Video MP4</span>
      </button>

      <button
        type="button"
        role="tab"
        aria-selected={selected === 'mp3'}
        className={`editorial-tab-btn ${selected === 'mp3' ? 'active' : ''}`}
        onClick={() => handleSelect('mp3')}
        disabled={disabled}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M9 18V5l12-2v13" />
          <circle cx="6" cy="18" r="3" />
          <circle cx="18" cy="16" r="3" />
        </svg>
        <span>Audio MP3</span>
      </button>

      <button
        type="button"
        role="tab"
        aria-selected={selected === 'thumbnail'}
        className={`editorial-tab-btn ${selected === 'thumbnail' ? 'active' : ''}`}
        onClick={() => handleSelect('thumbnail')}
        disabled={disabled}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <polyline points="21 15 16 10 5 21" />
        </svg>
        <span>Cover Art</span>
      </button>
    </div>
  );
};
