import React from 'react';

export interface StepItem {
  title: string;
  description: string;
}

export interface HowItWorksProps {
  steps?: StepItem[];
  platform?: 'youtube' | 'instagram' | 'all' | string;
}

const DEFAULT_STEPS: StepItem[] = [
  {
    title: 'Copy Media Link',
    description: 'Open YouTube or Instagram, tap Share, and copy the video or Reel URL to your clipboard.',
  },
  {
    title: 'Paste & Search',
    description: 'Insert the link into MediaFlow’s search bar and tap Search to parse metadata instantly.',
  },
  {
    title: 'Choose Format & Save',
    description: 'Select 1080p, 720p, or 320kbps MP3 audio, and tap Download to save straight to your device.',
  },
];

const STEP_IMAGES = [
  'https://lh3.googleusercontent.com/aida/AEtjO1URJ0efRg35HPfGL1hjDbhUWqCE-a8n4fOC2R_ykNFMadz4nLwvT_N8kKJGowo8AN9Lgaa1YoYIrR6xACPwsdawBkv53-QawFa--vTZmU3oBOoEL6KelK5kOUx01VcqpIshnpfLmjYOPl-5U8hdgoWhnkvJ-8zhu3gMDgR8seVPPO9RLvN_P7pdT0AdTfUIHvuR8e1f04Xs8JEadUzLg-SAZ_c0EGqFm5s2dvTltTPlzbepZgbdDA9OGWA',
  'https://lh3.googleusercontent.com/aida/AEtjO1V3K2wT55OmR6Vqr0vKpVvp7Tq8876ZhXCAc6OXca9i4fwHCK1Xqh0Etfq-8bPVwtOMwqswEWysTSAFf8cEq-MUl7EsrYky61kId38WWl-xLKRuoO8FAGEzKMGWXpNNkvaEznZ_V3-zgiYk0tATevq4xMHxLNTIbsvWkDwRKW80yCosxa4Q5cLVTm6Fd7kvsippV6gkbnHGS1kT6xx80mH-9fxGRWaFLgIAU4L_QVpeKGCL_qXuG_pMbqk',
  'https://lh3.googleusercontent.com/aida/AEtjO1Uh2T5rvxjIijjbnBUGMrKgCL9dI_HHA04B8yO5iIxvOOdNB2LSIqn0f4SvKoDIWB-obnt8c9mzNjoKfsHHriDiOA5DuKKbSOf0dhSkmQGPGwXf9YHEtpdCjFXn9yZCDeFCYJuoPWNsgtQcODZ6-kEPSOO7cMrxuMjXfeelW5T3_tyGYH8eAt7kMfR03rpXWRDEms_l0ZZqo7Z2IIjcjwk-9QP_S0Hux3jszJHhnO1YgoGG9iwL5HT6NkY',
];

export const HowItWorks: React.FC<HowItWorksProps> = ({
  steps = DEFAULT_STEPS,
}) => {
  return (
    <section className="how-it-works-section" id="how-it-works" aria-labelledby="how-it-works-heading">
      <div className="site-container">
        {/* Editorial Section Header */}
        <div className="section-header-editorial">
          <span className="section-eyebrow">Effortless Process</span>
          <h2 id="how-it-works-heading" className="section-h2-editorial">
            Three steps to offline freedom.
          </h2>
          <p className="section-subtitle-editorial">
            Compatible with any desktop browser, iPhone Camera Roll, and Android Files without installs.
          </p>
        </div>

        {/* 3-Column Visual Step Cards */}
        <div className="how-it-works-grid">
          {/* Step 1 */}
          <div className="editorial-step-card">
            <div className="step-top-row">
              <span className="step-num-display">01</span>
              <span className="step-tag-mono">Copy</span>
            </div>
            <div className="step-img-box">
              <img
                src={STEP_IMAGES[0]}
                alt="Step 1: Copy media link"
                className="step-preview-img"
                loading="lazy"
                onError={(e) => {
                  // Fallback to placeholder if image link fails
                  e.currentTarget.style.display = 'none';
                }}
              />
            </div>
            <h3 className="step-title-editorial">{steps[0]?.title || DEFAULT_STEPS[0].title}</h3>
            <p className="step-desc-editorial">{steps[0]?.description || DEFAULT_STEPS[0].description}</p>
            <div className="step-bottom-hint">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
              </svg>
              <span>Share → Copy Link</span>
            </div>
          </div>

          {/* Step 2 */}
          <div className="editorial-step-card">
            <div className="step-top-row">
              <span className="step-num-display">02</span>
              <span className="step-tag-mono">Paste</span>
            </div>
            <div className="step-img-box">
              <img
                src={STEP_IMAGES[1]}
                alt="Step 2: Paste link and search"
                className="step-preview-img"
                loading="lazy"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            </div>
            <h3 className="step-title-editorial">{steps[1]?.title || DEFAULT_STEPS[1].title}</h3>
            <p className="step-desc-editorial">{steps[1]?.description || DEFAULT_STEPS[1].description}</p>
            <div className="step-bottom-hint">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <rect x="2" y="4" width="20" height="16" rx="2" />
                <path d="M6 8h.01M10 8h.01M14 8h.01M18 8h.01M6 12h.01M10 12h.01M14 12h.01M18 12h.01M8 16h8" />
              </svg>
              <span>Instant URL Resolve</span>
            </div>
          </div>

          {/* Step 3 */}
          <div className="editorial-step-card">
            <div className="step-top-row">
              <span className="step-num-display">03</span>
              <span className="step-tag-mono">Save</span>
            </div>
            <div className="step-img-box">
              <img
                src={STEP_IMAGES[2]}
                alt="Step 3: Select quality and download"
                className="step-preview-img"
                loading="lazy"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            </div>
            <h3 className="step-title-editorial">{steps[2]?.title || DEFAULT_STEPS[2].title}</h3>
            <p className="step-desc-editorial">{steps[2]?.description || DEFAULT_STEPS[2].description}</p>
            <div className="step-bottom-hint verified">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span>Clean direct MP4/MP3</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
