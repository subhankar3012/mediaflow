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
      isToolPage: url === '/' || url.startsWith('/youtube-') || url.startsWith('/instagram-'),
    });
  } else if (url === '/404') {
    headTags = `
    <title>Page Not Found (404) - MediaFlow</title>
    <meta name="robots" content="noindex, follow" />
    <meta name="description" content="The page you requested could not be found. Return to MediaFlow to download YouTube and Instagram videos." />
    `.trim();
  }

  return { html, headTags };
}

export const routes = Object.keys(SEO_PAGES);
