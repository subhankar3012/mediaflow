import React from 'react';
import { appConfig } from '../../config/appConfig';

export interface AdSlotProps {
  position?: 'top' | 'between' | 'content' | 'bottom';
  slotType?: 'top' | 'between' | 'content' | 'bottom' | string;
  slotId?: string;
  label?: string;
  className?: string;
}

export const AdSlot: React.FC<AdSlotProps> = ({
  position,
  slotType,
  slotId,
  label = 'Sponsored Reserved Placement',
  className = '',
}) => {
  if (!appConfig.enableAds) {
    return null;
  }

  const effectivePos = position || slotType || 'content';

  return (
    <aside
      id={slotId}
      className={`editorial-ad-slot ${effectivePos} ${className}`.trim()}
      aria-label={label}
      role="complementary"
    >
      <div className="editorial-ad-inner">
        <span className="editorial-ad-tag font-mono">SPONSORED RESERVED PLACEMENT</span>
        <p className="editorial-ad-sub">Compliant, non-intrusive responsive slot (728x90 / 320x100)</p>
      </div>
    </aside>
  );
};
