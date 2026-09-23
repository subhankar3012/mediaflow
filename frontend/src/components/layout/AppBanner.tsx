import React, { useState, useEffect } from 'react';

export interface AppBannerProps {
  onOpenModal: () => void;
}

const STORAGE_KEY = 'mediaflow_app_banner_dismissed';

export const AppBanner: React.FC<AppBannerProps> = ({ onOpenModal }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    try {
      const isDismissed = localStorage.getItem(STORAGE_KEY);
      if (!isDismissed) {
        setIsVisible(true);
      }
    } catch {
      // In case localStorage is blocked/disabled
      setIsVisible(true);
    }
  }, []);

  const handleDismiss = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsVisible(false);
    try {
      localStorage.setItem(STORAGE_KEY, 'true');
    } catch {
      // Ignore localStorage write errors
    }
  };

  if (!isVisible) return null;

  return (
    <aside className="app-promo-strip" aria-label="MediaFlow Android App Announcement">
      <div className="app-promo-inner">
        <div className="app-promo-left">
          <span className="app-promo-badge">
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="currentColor"
              aria-hidden="true"
              style={{ display: 'inline-block', verticalAlign: '-1px' }}
            >
              {/* Android Robot SVG Icon */}
              <path d="M17.523 15.3414c-.5511 0-.9993-.4486-.9993-.9997s.4482-.9993.9993-.9993c.551 0 .9993.4482.9993.9993 0 .5511-.4483.9997-.9993.9997m-11.046 0c-.5511 0-.9993-.4486-.9993-.9997s.4482-.9993.9993-.9993c.5511 0 .9993.4482.9993.9993 0 .5511-.4482.9997-.9993.9997m11.4045-6.02l1.9973-3.4592a.416.416 0 00-.1523-.5676.416.416 0 00-.5676.1523l-2.0223 3.503C15.5902 8.4116 13.8533 8 12 8s-3.5902.4116-5.1369.9499L4.8408 5.4469a.416.416 0 00-.5676-.1523.416.416 0 00-.1523.5676l1.9973 3.4592C2.6889 11.1867.3432 14.6589 0 18.761h24c-.3432-4.1021-2.6889-7.5743-6.1185-9.4396" />
            </svg>
            Android App
          </span>
          <p className="app-promo-text">
            Want <strong>4K 60FPS</strong> Ultra HD &amp; 1-Tap Share downloads? Get the free <strong>MediaFlow Android App</strong>.
          </p>
        </div>

        <div className="app-promo-right">
          <button
            type="button"
            className="app-promo-cta-btn"
            onClick={onOpenModal}
            aria-label="Download MediaFlow Android App APK"
          >
            <span>Get Free APK</span>
            <svg
              width="13"
              height="13"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M5 12h14" />
              <path d="M12 5l7 7-7 7" />
            </svg>
          </button>
          <button
            type="button"
            className="app-promo-close-btn"
            onClick={handleDismiss}
            aria-label="Dismiss banner"
            title="Dismiss announcement"
          >
            ✕
          </button>
        </div>
      </div>
    </aside>
  );
};
