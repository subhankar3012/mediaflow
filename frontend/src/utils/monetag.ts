/**
 * Monetag Manual Ad Suite
 * - In-Page Push: Zone 11880513 (https://nap5k.com/tag.min.js)
 * - Vignette Banner: Zone 11880602 (https://n6wxm.com/vignette.min.js)
 * - On-Click Popunder: Zone 11880603 (https://al5sm.com/tag.min.js)
 * - Direct Link: https://omg10.com/4/11880595
 */

import { appConfig } from '../config/appConfig';

function injectMonetagScript(src: string, zone: string): void {
  if (typeof window === 'undefined') return;
  if (document.querySelector(`script[data-zone="${zone}"]`)) return;

  try {
    const s = document.createElement('script');
    s.dataset.zone = zone;
    s.src = src;
    s.async = true;
    s.setAttribute('data-cfasync', 'false');
    const target = [document.documentElement, document.body, document.head].filter(Boolean).pop();
    if (target) {
      target.appendChild(s);
    }
  } catch (err) {
    console.warn(`Monetag zone ${zone} injection error:`, err);
  }
}

/** In-Page Push (floating toast alert, low annoyance) */
export function loadInPagePush(): void {
  injectMonetagScript('https://nap5k.com/tag.min.js', '11880513');
}

/** Vignette Banner (fullscreen modal on transitions, high CPM) */
export function loadVignette(): void {
  if (typeof window === 'undefined') return;
  if (typeof (window as any).initVignette === 'function') {
    try {
      (window as any).initVignette(11880602);
      return;
    } catch (_) {}
  }
  injectMonetagScript('https://n6wxm.com/vignette.min.js', '11880602');
}

/** On-Click Popunder (new tab on user click) */
export function loadOnClick(): void {
  injectMonetagScript('https://al5sm.com/tag.min.js', '11880603');
}

/** Direct Link trigger */
export function triggerMonetagDirectLink(): void {
  if (typeof window === 'undefined') return;
  const link = appConfig.monetagDirectLink || 'https://omg10.com/4/11880595';
  try {
    window.open(link, '_blank', 'noopener,noreferrer');
  } catch (err) {
    console.warn('Monetag direct link open error:', err);
  }
}

export function triggerMonetagAd(): void {
  // Safe alias for backward compatibility
  loadVignette();
}




