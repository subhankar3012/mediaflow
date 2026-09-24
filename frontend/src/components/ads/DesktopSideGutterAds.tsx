import React, { useState } from 'react';
import { appConfig } from '../../config/appConfig';
import { AdsterraBanner } from './AdsterraBanner';

export const DesktopSideGutterAds: React.FC = () => {
  const [leftDismissed, setLeftDismissed] = useState(false);
  const [rightDismissed, setRightDismissed] = useState(false);

  if (!appConfig.enableAds) {
    return null;
  }

  return (
    <>
      {/* 1. Left Desktop Gutter Rail (160x600 Skyscraper) */}
      {!leftDismissed && (
        <aside
          className="desktop-gutter-rail desktop-gutter-left"
          aria-label="Sponsored Content Left"
          role="complementary"
        >
          <div className="desktop-gutter-card">
            <div className="desktop-gutter-header">
              <span className="desktop-gutter-badge">
                <span className="desktop-gutter-badge-dot" />
                <span>Ad</span>
              </span>
              <button
                type="button"
                className="desktop-gutter-close"
                onClick={() => setLeftDismissed(true)}
                title="Dismiss ad"
                aria-label="Dismiss ad"
              >
                ✕
              </button>
            </div>
            <div className="desktop-gutter-body">
              <AdsterraBanner slotType="skyscraper-left" slotId="desktop-gutter-left-banner" hideLabel />
            </div>
          </div>
        </aside>
      )}

      {/* 2. Right Desktop Gutter Rail (160x300 Skyscraper) */}
      {!rightDismissed && (
        <aside
          className="desktop-gutter-rail desktop-gutter-right"
          aria-label="Sponsored Content Right"
          role="complementary"
        >
          <div className="desktop-gutter-card">
            <div className="desktop-gutter-header">
              <span className="desktop-gutter-badge">
                <span className="desktop-gutter-badge-dot" />
                <span>Ad</span>
              </span>
              <button
                type="button"
                className="desktop-gutter-close"
                onClick={() => setRightDismissed(true)}
                title="Dismiss ad"
                aria-label="Dismiss ad"
              >
                ✕
              </button>
            </div>
            <div className="desktop-gutter-body">
              <AdsterraBanner slotType="skyscraper-right" slotId="desktop-gutter-right-banner" hideLabel />
            </div>
          </div>
        </aside>
      )}
    </>
  );
};
