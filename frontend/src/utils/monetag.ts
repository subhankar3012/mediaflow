/**
 * Monetag Ad Integration
 * Configured in index.html to load automatically 15s after user enters website.
 * triggerMonetagAd ensures singleton safety if ever called manually.
 */

let isMonetagLoaded = false;

export function triggerMonetagAd(): void {
  if (typeof window === 'undefined' || isMonetagLoaded) return;
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
    console.warn('Monetag injection notice:', err);
  }
}


