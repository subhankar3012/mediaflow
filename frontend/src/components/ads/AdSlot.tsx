import React, { useEffect, useRef } from 'react';
import { appConfig } from '../../config/appConfig';

declare global {
  interface Window {
    adsbygoogle?: any[];
  }
}

export interface AdSlotProps {
  position?: 'top' | 'between' | 'content' | 'bottom';
  slotType?: 'top' | 'between' | 'content' | 'bottom' | string;
  slotId?: string;
  adUnitId?: string;
  label?: string;
  className?: string;
}

export const AdSlot: React.FC<AdSlotProps> = ({
  position,
  slotType,
  slotId,
  adUnitId,
  label = 'Advertisement',
  className = '',
}) => {
  const adRef = useRef<HTMLModElement | null>(null);
  const pushedRef = useRef(false);

  useEffect(() => {
    if (!appConfig.enableAds || !adUnitId || pushedRef.current) {
      return;
    }

    try {
      if (typeof window !== 'undefined' && adRef.current) {
        if (!adRef.current.getAttribute('data-adsbygoogle-status')) {
          (window.adsbygoogle = window.adsbygoogle || []).push({});
          pushedRef.current = true;
        }
      }
    } catch (e) {
      console.warn('AdSense unit push skipped or failed:', e);
    }
  }, [adUnitId]);

  if (!appConfig.enableAds) {
    return null;
  }

  const effectivePos = position || slotType || 'content';

  if (adUnitId) {
    return (
      <aside
        id={slotId}
        className={`editorial-ad-slot ${effectivePos} ${className}`.trim()}
        aria-label={label}
        role="complementary"
      >
        <ins
          ref={adRef}
          className="adsbygoogle"
          style={{ display: 'block' }}
          data-ad-client={appConfig.adSenseClientId}
          data-ad-slot={adUnitId}
          data-ad-format="auto"
          data-full-width-responsive="true"
        />
      </aside>
    );
  }

  return (
    <aside
      id={slotId}
      className={`editorial-ad-slot ${effectivePos} ${className}`.trim()}
      aria-label={label}
      role="complementary"
    />
  );
};
