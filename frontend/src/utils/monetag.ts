/**
 * Dynamic Monetag Ad Loader
 * Delays ad execution so users aren't spammed on page entry.
 * Activates either via homepage timer (8s) or when user triggers a download.
 */

let isMonetagLoaded = false;

export function triggerMonetagAd(): void {
  if (typeof window === 'undefined' || isMonetagLoaded) {
    return;
  }

  // Check if tag already exists in DOM
  if (document.querySelector('script[data-zone="285252"]')) {
    isMonetagLoaded = true;
    return;
  }

  try {
    const script = document.createElement('script');
    script.src = 'https://quge5.com/88/tag.min.js';
    script.setAttribute('data-zone', '285252');
    script.async = true;
    script.setAttribute('data-cfasync', 'false');
    document.head.appendChild(script);
    isMonetagLoaded = true;
  } catch (err) {
    console.warn('Monetag dynamic injection notice:', err);
  }
}
