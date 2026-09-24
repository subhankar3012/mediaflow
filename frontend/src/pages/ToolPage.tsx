import React from 'react';
import type { PageSEO } from '../config/seoContent';
import type { OutputType } from '../api/types';
import type { StepItem } from '../components/seo/HowItWorks';
import { HeadMeta } from '../components/seo/HeadMeta';
import { PlatformThemeProvider } from '../components/theme/PlatformThemeProvider';
import { DownloaderTool } from '../components/downloader/DownloaderTool';
import { HowItWorks } from '../components/seo/HowItWorks';
import { FeatureGrid } from '../components/seo/FeatureGrid';
import { FAQSection } from '../components/seo/FAQSection';
import { RelatedTools } from '../components/seo/RelatedTools';
import { AdSlot } from '../components/ads/AdSlot';
import { AnimatedHeroTitle } from '../components/hero/AnimatedHeroTitle';
import { Breadcrumbs } from '../components/seo/Breadcrumbs';
import { TechnicalSpecsTable } from '../components/seo/TechnicalSpecsTable';
import { DeviceGuidance } from '../components/seo/DeviceGuidance';

export interface ToolPageProps {
  page: PageSEO;
}

export const ToolPage: React.FC<ToolPageProps> = ({ page }) => {
  const defaultOutputType: OutputType = page.path === '/youtube-to-mp3' ? 'mp3' : 'mp4';

  const customSteps: StepItem[] | undefined =
    page.howItWorks && page.howItWorks.length === 3
      ? [
          { title: 'Copy Media Link', description: page.howItWorks[0] },
          { title: 'Paste & Search', description: page.howItWorks[1] },
          { title: 'Choose Format & Save', description: page.howItWorks[2] },
        ]
      : undefined;

  return (
    <PlatformThemeProvider platform={page.platform}>
      <HeadMeta
        title={page.title}
        description={page.metaDescription}
        canonicalPath={page.path}
        breadcrumbs={page.breadcrumbs}
        isToolPage={true}
      />

      {/* Semantic Breadcrumbs (Hierarchy & SEO) */}
      <Breadcrumbs items={page.breadcrumbs} />

      {/* Editorial Centered Hero Section */}
      <section className="hero-editorial-section">
        <div className="site-container-narrow text-center">
          {/* Top Live / Brand Badge */}
          {page.path === '/' ? (
            <div className="hero-brand-badge font-mono">
              <img src="/brand-icon.png" alt="" width="18" height="18" className="hero-brand-badge-img" />
              <span className="hero-brand-badge-title">MediaFlow</span>
              <span className="meta-sep">•</span>
              <span className="hero-brand-badge-tag">Free Online Downloader</span>
            </div>
          ) : (
            <div className="hero-live-badge font-mono">
              <span className="live-dot" />
              <span>Direct Media Extraction • Zero Loss</span>
            </div>
          )}

          {/* Centered Editorial H1 */}
          {page.path === '/' ? (
            <AnimatedHeroTitle fallbackTitle={page.h1} />
          ) : (
            <h1 className="hero-editorial-h1">{page.h1}</h1>
          )}

          {/* Subtitle */}
          <p className="hero-editorial-sub">{page.subtitle}</p>

          {/* Trust Signals Row */}
          <div className="hero-trust-row font-mono">
            <span className="hero-trust-item">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>
              100% Free
            </span>
            <span className="meta-sep">•</span>
            <span className="hero-trust-item">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>
              No Registration
            </span>
            <span className="meta-sep">•</span>
            <span className="hero-trust-item">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>
              Verified SSL
            </span>
          </div>
        </div>
      </section>

      {/* Centered Downloader Tool (600–650px wide) - Kept Prominently Above the Fold */}
      <div className="site-container-tool">
        <DownloaderTool
          defaultOutputType={defaultOutputType}
          placeholder={page.placeholder}
        />
      </div>

      {/* Minimal Top Ad Placement */}
      <div className="site-container-tool">
        <AdSlot slotId="ad-top-banner" slotType="top" label="Sponsored Placement" />
      </div>

      {/* Visual How It Works */}
      <HowItWorks steps={customSteps} platform={page.platform} />

      {/* Ad after How It Works */}
      <div className="site-container-tool">
        <AdSlot slotId="ad-after-howitworks" slotType="banner468" label="Sponsored Placement" />
      </div>

      {/* Technical Specifications Comparison Table */}
      <TechnicalSpecsTable
        platform={page.platform}
        title={page.specsTitle}
        description={page.specsDescription}
      />

      {/* Sponsored Recommendations after Specs */}
      <div className="site-container-tool">
        <AdSlot slotId="ad-after-specs" slotType="native" label="Sponsored Recommendations" />
      </div>

      {/* Device-Specific OS Guidance (iOS Safari, Android, Desktop) */}
      <DeviceGuidance />

      {/* Ad after Device Guidance */}
      <div className="site-container-tool">
        <AdSlot slotId="ad-between-tool" slotType="between" label="Sponsored Placement" />
      </div>

      {/* Feature Grid (Clean Minimal Cards) */}
      {page.features && page.features.length > 0 && (
        <FeatureGrid features={page.features} />
      )}

      {/* High-engagement Rectangle Ad after Feature Grid */}
      <div className="site-container-tool">
        <AdSlot slotId="ad-after-features" slotType="rectangle" label="Sponsored Placement" />
      </div>

      {/* Accordion FAQ */}
      {page.faqs && page.faqs.length > 0 && (
        <FAQSection faqs={page.faqs} />
      )}

      {/* Bottom Ad after FAQ */}
      <div className="site-container-tool">
        <AdSlot slotId="ad-bottom-leaderboard" slotType="bottom" label="Sponsored Placement" />
      </div>

      {/* Specialized Converters Grid */}
      <RelatedTools currentPath={page.path} />

      {/* Ad after Related Tools (before footer) */}
      <div className="site-container-tool">
        <AdSlot slotId="ad-after-related" slotType="banner468" label="Sponsored Placement" />
      </div>
    </PlatformThemeProvider>
  );
};
