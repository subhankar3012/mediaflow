import React from 'react';
import { Router, useRouter } from './router/Router';
import { Layout } from './components/layout/Layout';
import { ToolPage } from './pages/ToolPage';
import { SimpleContentPage } from './pages/SimpleContentPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { SEO_PAGES } from './config/seoContent';

const AppRoutes: React.FC = () => {
  const { currentPath } = useRouter();

  // Normalize trailing slash (except root '/')
  const normalizedPath = currentPath.length > 1 && currentPath.endsWith('/')
    ? currentPath.slice(0, -1)
    : currentPath;

  // Tool / Downloader Pages
  const toolPaths = [
    '/',
    '/youtube-video-downloader',
    '/youtube-to-mp3',
    '/youtube-to-mp4',
    '/instagram-downloader',
    '/instagram-reels-downloader',
  ];

  if (toolPaths.includes(normalizedPath) && SEO_PAGES[normalizedPath]) {
    return <ToolPage page={SEO_PAGES[normalizedPath]} />;
  }

  // Informational / Legal / FAQ Content Pages
  const contentPaths = [
    '/faq',
    '/about',
    '/contact',
    '/privacy-policy',
    '/terms',
  ];

  if (contentPaths.includes(normalizedPath) && SEO_PAGES[normalizedPath]) {
    return <SimpleContentPage page={SEO_PAGES[normalizedPath]} />;
  }

  // 404 Fallback
  return <NotFoundPage />;
};

export default function App({ initialPath }: { initialPath?: string } = {}) {
  return (
    <Router initialPath={initialPath}>
      <Layout>
        <AppRoutes />
      </Layout>
    </Router>
  );
}
