import React, { memo } from 'react';
import { appConfig } from '../../config/appConfig';
import { AdsterraBanner } from './AdsterraBanner';

export interface AdSlotProps {
  position?:
    | 'top'
    | 'between'
    | 'content'
    | 'bottom'
    | 'processing'
    | 'banner468'
    | 'rectangle'
    | 'native'
    | 'skyscraper'
    | string;
  slotType?:
    | 'top'
    | 'between'
    | 'content'
    | 'bottom'
    | 'processing'
    | 'banner468'
    | 'rectangle'
    | 'native'
    | 'skyscraper'
    | string;
  slotId?: string;
  adUnitId?: string;
  label?: string;
  className?: string;
}

export const AdSlot: React.FC<AdSlotProps> = memo(({
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
});
