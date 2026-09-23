import { appConfig, getCanonicalUrl } from '../config/appConfig';

export interface BreadcrumbItem {
  name: string;
  path: string;
}

export interface GenerateSeoOptions {
  title: string;
  description: string;
  canonicalPath: string;
  ogType?: string;
  ogImage?: string;
  breadcrumbs?: BreadcrumbItem[];
  isToolPage?: boolean;
}

export function generateBreadcrumbsSchema(breadcrumbs: BreadcrumbItem[], canonicalDomain: string = appConfig.canonicalDomain) {
  if (!breadcrumbs || breadcrumbs.length === 0) return null;

  return {
    '@type': 'BreadcrumbList',
    itemListElement: breadcrumbs.map((crumb, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: crumb.name,
      item: getCanonicalUrl(crumb.path, canonicalDomain),
    })),
  };
}

export function generateJsonLdGraph(options: GenerateSeoOptions, canonicalDomain: string = appConfig.canonicalDomain) {
  const canonicalUrl = getCanonicalUrl(options.canonicalPath, canonicalDomain);
  const graph: any[] = [];

  // 1. WebSite Schema (Google Site Name signals)
  graph.push({
    '@type': 'WebSite',
    '@id': `${canonicalDomain}/#website`,
    url: canonicalDomain,
    name: appConfig.brandName,
    alternateName: ['Media Flow', 'MediaFlow', 'MediaFlow Downloader', 'MediaFlow App'],
    description: appConfig.brandTagline,
    inLanguage: 'en',
  });

  // 2. Organization Schema (authentic brand signals)
  graph.push({
    '@type': 'Organization',
    '@id': `${canonicalDomain}/#organization`,
    name: appConfig.brandName,
    url: canonicalDomain,
    logo: {
      '@type': 'ImageObject',
      url: `${canonicalDomain}/brand-icon.png`,
    },
  });

  // 3. WebApplication Schema for tool pages (genuine free pricing, NO fake ratings)
  if (options.isToolPage || options.canonicalPath === '/' || options.canonicalPath.startsWith('/youtube-') || options.canonicalPath.startsWith('/instagram-')) {
    const appName = options.canonicalPath === '/'
      ? 'MediaFlow — Free Online Video & Audio Downloader'
      : options.title.split(' — ')[1] || options.title;

    graph.push({
      '@type': 'WebApplication',
      '@id': `${canonicalUrl}/#webapp`,
      url: canonicalUrl,
      name: appName,
      applicationCategory: 'MultimediaApplication',
      operatingSystem: 'All',
      browserRequirements: 'Requires JavaScript. Requires HTML5.',
      offers: {
        '@type': 'Offer',
        price: '0.00',
        priceCurrency: 'USD',
      },
      featureList: [
        'High-Definition Video Extraction (up to 1080p Full HD)',
        'Direct MP3 Audio Conversion',
        'Mobile Optimized (iOS Safari & Android)',
        'Zero Account Registration Required',
        'Private Cloud Processing with Automatic 30-Minute File Purge',
      ],
    });
  }

  // 3. BreadcrumbList Schema (if breadcrumbs provided and not home)
  if (options.breadcrumbs && options.breadcrumbs.length > 1) {
    const breadcrumbSchema = generateBreadcrumbsSchema(options.breadcrumbs, canonicalDomain);
    if (breadcrumbSchema) {
      graph.push(breadcrumbSchema);
    }
  }

  return {
    '@context': 'https://schema.org',
    '@graph': graph,
  };
}

export function buildHeadTagsHtml(options: GenerateSeoOptions, canonicalDomain: string = appConfig.canonicalDomain): string {
  const canonicalUrl = getCanonicalUrl(options.canonicalPath, canonicalDomain);
  const ogType = options.ogType || 'website';
  const defaultOgImage = `${canonicalDomain}/og-image.png`;
  const ogImage = options.ogImage || defaultOgImage;
  const jsonLd = generateJsonLdGraph(options, canonicalDomain);

  return `
    <title>${escapeHtml(options.title)}</title>
    <meta name="description" content="${escapeHtml(options.description)}" />
    <link rel="canonical" href="${escapeHtml(canonicalUrl)}" />
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="${escapeHtml(ogType)}" />
    <meta property="og:site_name" content="${escapeHtml(appConfig.brandName)}" />
    <meta property="og:url" content="${escapeHtml(canonicalUrl)}" />
    <meta property="og:title" content="${escapeHtml(options.title)}" />
    <meta property="og:description" content="${escapeHtml(options.description)}" />
    <meta property="og:image" content="${escapeHtml(ogImage)}" />
    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:url" content="${escapeHtml(canonicalUrl)}" />
    <meta name="twitter:title" content="${escapeHtml(options.title)}" />
    <meta name="twitter:description" content="${escapeHtml(options.description)}" />
    <meta name="twitter:image" content="${escapeHtml(ogImage)}" />
    <!-- Structured Data -->
    <script type="application/ld+json" id="json-ld-schema">
${JSON.stringify(jsonLd, null, 2)}
    </script>
  `.trim();
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
