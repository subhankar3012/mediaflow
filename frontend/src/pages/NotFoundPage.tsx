import React from 'react';
import { HeadMeta } from '../components/seo/HeadMeta';
import { Link } from '../router/Link';

export const NotFoundPage: React.FC = () => {
  return (
    <>
      <HeadMeta
        title="404 - Page Not Found | MediaFlow"
        description="The requested page could not be found. Return to MediaFlow home to convert and download media."
        canonicalPath="/404"
      />
      <div className="site-container not-found-container">
        <div className="not-found-code">404</div>
        <h1 className="hero-h1" style={{ fontSize: '2rem', marginBottom: '1rem' }}>
          Page Not Found
        </h1>
        <p className="hero-subtitle" style={{ marginBottom: '2rem' }}>
          The page you are looking for doesn't exist, has been moved, or the link may be mistyped.
        </p>
        <div className="not-found-actions">
          <Link to="/" className="btn-primary">Back to Home</Link>
          <Link to="/youtube-video-downloader" className="btn-secondary">YouTube Downloader</Link>
        </div>
      </div>
    </>
  );
};
