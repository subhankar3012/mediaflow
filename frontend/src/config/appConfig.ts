export interface AppConfig {
  brandName: string;
  brandTagline: string;
  canonicalDomain: string;
  enableAds: boolean;
  adSenseClientId: string;
  enableInterstitial: boolean;
  interstitialCountdownSeconds: number;
}

const configuredDomain =
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_CANONICAL_DOMAIN) ||
  (typeof (globalThis as any).process !== 'undefined' && (globalThis as any).process?.env?.VITE_CANONICAL_DOMAIN) ||
  'https://download.strengerchat.in';

export const appConfig: AppConfig = {
  brandName: 'MediaFlow',
  brandTagline: 'Download YouTube & Instagram Videos Free Without Watermark',
  canonicalDomain: configuredDomain.replace(/\/+$/, ''),
  enableAds: true, // Reserves space and provides ad containers without deceptive UI
  adSenseClientId: 'ca-pub-9604961997726378',
  enableInterstitial: false, // Configurable single-step preparation flow; off by default for clean UX
  interstitialCountdownSeconds: 3,
};

export function getCanonicalUrl(path: string, domain: string = appConfig.canonicalDomain): string {
  const cleanDomain = domain.replace(/\/+$/, '');
  if (!path || path === '/') {
    return cleanDomain;
  }
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  const normalizedPath = cleanPath.length > 1 && cleanPath.endsWith('/') ? cleanPath.slice(0, -1) : cleanPath;
  return `${cleanDomain}${normalizedPath}`;
}
