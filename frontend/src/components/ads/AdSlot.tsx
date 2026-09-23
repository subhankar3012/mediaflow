import React from 'react';
import { appConfig } from '../../config/appConfig';
import { AdsterraBanner } from './AdsterraBanner';

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
  className = '',
}) => {
  if (!appConfig.enableAds) {
    return null;
  }

  const effectivePos = position || slotType || 'top';

  return (
    <AdsterraBanner
      slotType={effectivePos}
      slotId={slotId}
      className={className}
    />
  );
};
