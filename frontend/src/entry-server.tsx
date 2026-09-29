import { StrictMode } from 'react';
import { renderToString } from 'react-dom/server';
import App from './App';
import { SEO_PAGES } from './config/seoContent';
import { buildHeadTagsHtml } from './utils/seoHelpers';

export function render(url: string) {
  const html = renderToString(
    <StrictMode>
      <App initialPath={url} />
    </StrictMode>
  );

  const page = SEO_PAGES[url];
  let headTags = '';
  if (page) {
    headTags = buildHeadTagsHtml({
      title: page.title,
      description: page.metaDescription,
      canonicalPath: page.path,
      breadcrumbs: page.breadcrumbs,
      isToolPage: url === '/' || url.startsWith('/youtube-') || url.startsWith('/instagram-') || url.startsWith('/x-') || url.startsWith('/facebook-') || url.startsWith('/pinterest-') || url.startsWith('/reddit-'),
    });
  } else if (url === '/download') {
    headTags = `
    <title>Download MediaFlow for Android (Official APK • v1.5.7)</title>
    <meta name="description" content="Download MediaFlow Android App for high-speed 4K/1080p video and photo downloads from YouTube, Instagram, X/Twitter, and Reddit." />
    <link rel="canonical" href="https://download.strengerchat.in/download" />
    <meta property="og:title" content="Download MediaFlow Android App (v1.5.7)" />
    <meta property="og:description" content="Download MediaFlow Android App for high-speed video and photo downloads." />
    <meta property="og:type" content="website" />
    <meta property="og:url" content="https://download.strengerchat.in/download" />
    <meta name="twitter:card" content="summary" />
    <meta name="twitter:title" content="Download MediaFlow Android App (v1.5.7)" />
    <meta name="twitter:description" content="Download MediaFlow Android App for high-speed video and photo downloads." />
    `.trim();
  } else if (url === '/404') {
    headTags = `
    <title>Page Not Found (404) - MediaFlow</title>
    <meta name="robots" content="noindex, follow" />
    <meta name="description" content="The page you requested could not be found. Return to MediaFlow to download YouTube and Instagram videos." />
    `.trim();
  }

  return { html, headTags };
}

export const routes = [...Object.keys(SEO_PAGES), '/download'];
