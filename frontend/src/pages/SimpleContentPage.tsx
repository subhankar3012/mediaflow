import React from 'react';
import type { PageSEO } from '../config/seoContent';
import { HeadMeta } from '../components/seo/HeadMeta';
import { FAQSection } from '../components/seo/FAQSection';
import { AdSlot } from '../components/ads/AdSlot';
import { Link } from '../router/Link';
import { appConfig } from '../config/appConfig';
import { PlatformThemeProvider } from '../components/theme/PlatformThemeProvider';
import { Breadcrumbs } from '../components/seo/Breadcrumbs';

export interface SimpleContentPageProps {
  page: PageSEO;
}

export const SimpleContentPage: React.FC<SimpleContentPageProps> = ({ page }) => {
  return (
    <PlatformThemeProvider platform={page.platform}>
      <HeadMeta
        title={page.title}
        description={page.metaDescription}
        canonicalPath={page.path}
        breadcrumbs={page.breadcrumbs}
        isToolPage={false}
      />

      <Breadcrumbs items={page.breadcrumbs} />

      <AdSlot slotId="ad-content-top" slotType="top" label="Advertisement" />

      <div className="site-container" style={{ padding: '2.5rem 1.25rem', maxWidth: '840px' }}>
        <h1 className="hero-h1" style={{ textAlign: 'left', marginBottom: '0.75rem' }}>
          {page.h1}
        </h1>
        <p className="hero-subtitle" style={{ textAlign: 'left', margin: '0 0 2rem 0' }}>
          {page.subtitle}
        </p>

        {page.path === '/about' && (
          <article className="content-article">
            <div style={{ marginBottom: '2rem', padding: '1rem 1.5rem', background: '#ffffff', borderRadius: 'var(--radius-xl)', border: '1px solid rgba(226, 232, 240, 0.8)', display: 'inline-block', boxShadow: 'var(--shadow-subtle)' }}>
              <img src="/logo-full.png" alt="MediaFlow - Your Media, Your Way" style={{ maxHeight: '52px', width: 'auto', display: 'block' }} />
            </div>

            <h2>Our Mission</h2>
            <p>
              {appConfig.brandName} is dedicated to providing internet users with a fast, safe, and dependable tool for converting and saving publicly accessible videos and audio for offline educational and personal use.
            </p>
            <p>
              We built our engine using modern streaming and media extraction technologies that process video files rapidly and reliably without forcing users through intrusive popups, deceptive links, or bloated software installers.
            </p>

            <h2>Engineered for Speed & Simplicity</h2>
            <p>
              Whether you are an educator preparing classroom material, a researcher analyzing video content, or an individual saving a memorable video for offline viewing during travel, our platform ensures seamless audio extraction and video downloads in multiple resolutions.
            </p>

            <h2>Respect for Creators & Copyright</h2>
            <p>
              We strongly support intellectual property rights and creative ownership. Our tool is intended strictly for personal, fair use archiving. We encourage all users to support original content creators by subscribing, liking, and engaging with their primary channels.
            </p>
          </article>
        )}

        {page.path === '/contact' && (
          <article className="content-article">
            <p>
              Have questions, feedback, bug reports, or feature requests? We would love to hear from you. Please reach out to our team using the channels below:
            </p>

            <div className="content-card">
              <h3>Customer Support & General Enquiries</h3>
              <p style={{ margin: 0 }}>
                Email:{' '}
                <a href="mailto:support@mediaflow.app">support@mediaflow.app</a>
              </p>
              <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                Response time: We strive to reply to all queries within 24 to 48 business hours.
              </p>
            </div>

            <div className="content-card">
              <h3>DMCA & Copyright Compliance</h3>
              <p style={{ margin: 0 }}>
                If you are a copyright holder wishing to request the removal or blocking of specific content URLs, please submit your notice to{' '}
                <a href="mailto:dmca@mediaflow.app">dmca@mediaflow.app</a>.
              </p>
            </div>
          </article>
        )}

        {page.path === '/privacy-policy' && (
          <article className="content-article">
            <p>Last updated: September 2026</p>
            <h2>1. Information We Collect</h2>
            <p>
              {appConfig.brandName} respects your privacy. We do not require users to create an account, provide names, or disclose email addresses to use our downloader service. We temporarily process the URLs submitted in order to extract metadata and provide download links.
            </p>
            <h2>2. Temporary File Storage & Retention</h2>
            <p>
              When a download conversion is processed, the resultant file is stored in temporary isolated storage and is automatically deleted after 30 minutes. We do not maintain permanent archives of processed media.
            </p>
            <h2>3. Cookies & Advertising</h2>
            <p>
              We use standard session cookies strictly necessary to maintain your conversion request state and session continuity. Third-party advertising partners, including Google AdSense, may use cookies or web beacons to serve personalized or contextual advertisements on our website.
            </p>
            <h2>4. Analytics & Log Data</h2>
            <p>
              Like most online services, we collect non-personally identifiable log information such as browser type, referring pages, timestamps, and general geographic region to ensure system stability, prevent malicious abuse, and optimize server performance.
            </p>
          </article>
        )}

        {page.path === '/terms' && (
          <article className="content-article">
            <p>Last updated: September 2026</p>
            <h2>1. Acceptance of Terms</h2>
            <p>
              By accessing or using {appConfig.brandName}, you agree to be bound by these Terms of Service. If you disagree with any portion of these terms, you may not use our service.
            </p>
            <h2>2. Permitted & Fair Use</h2>
            <p>
              {appConfig.brandName} is provided solely for personal, non-commercial, and educational use. Users must have the legal right or permission to download any material processed through our service. You agree not to use the service for infringing any copyright, trademark, or intellectual property rights.
            </p>
            <h2>3. Disclaimer of Warranties</h2>
            <p>
              The service is provided on an &quot;as is&quot; and &quot;as available&quot; basis without warranties of any kind. We do not guarantee uninterrupted access or that third-party video platforms will remain accessible.
            </p>
            <h2>4. Third-Party Links & Disclaimers</h2>
            <p>
              {appConfig.brandName} is an independent utility and is not affiliated, endorsed, or associated with YouTube, Google LLC, Instagram, or Meta Platforms, Inc.
            </p>
          </article>
        )}

        {page.path === '/faq' && (
          <div>
            <FAQSection faqs={page.faqs} />
            <div style={{ marginTop: '2.5rem', textAlign: 'center' }}>
              <Link to="/" className="btn-primary" style={{ display: 'inline-flex' }}>
                Go to Video Downloader
              </Link>
            </div>
          </div>
        )}
      </div>

      <AdSlot slotId="ad-content-bottom" slotType="bottom" label="Advertisement" />
    </PlatformThemeProvider>
  );
};
