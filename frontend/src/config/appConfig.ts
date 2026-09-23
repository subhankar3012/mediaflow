export interface AppConfig {
  brandName: string;
  brandTagline: string;
  canonicalDomain: string;
  enableAds: boolean;
  adsterraDirectLink: string;
  adsterraBanners: {
    leaderboard728x90: string;
    mobile320x50: string;
    rectangle300x250: string;
    banner468x60: string;
    skyscraper160x600: string;
    skyscraper160x300: string;
    nativeContainerId: string;
    nativeScriptSrc: string;
  };
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
  enableAds: true,
  adsterraDirectLink: 'https://www.profitableratecpmnetwork.com/ber0grk7?key=0b0e46dfb008c520f9fdf850820e8c9d',
  adsterraBanners: {
    leaderboard728x90: '20d268753690e18bcb7cb0d3a3d28e8f',
    mobile320x50: '078849d0d16d7514274d905b13b1ab2e',
    rectangle300x250: 'b14af57b2afcf5946cdc3469d15fb1bd',
    banner468x60: '4f969eeff776612d24bb4930a21a7713',
    skyscraper160x600: '75d42770ad9b0b3039cf57a7e55e9e62',
    skyscraper160x300: '2dc4ff74d0f64b72e28e643c3d1676d8',
    nativeContainerId: 'container-feae44703559111e89156a6f6e873e79',
    nativeScriptSrc: 'https://pl31478900.profitableratecpmnetwork.com/feae44703559111e89156a6f6e873e79/invoke.js',
  },
  enableInterstitial: true,
  interstitialCountdownSeconds: 5,
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
