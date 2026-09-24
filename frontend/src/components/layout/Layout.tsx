import React from 'react';
import { Header } from './Header';
import { Footer } from './Footer';
import { useRouter } from '../../router/Router';
import { PlatformThemeProvider } from '../theme/PlatformThemeProvider';
import { DesktopSideGutterAds } from '../ads/DesktopSideGutterAds';

export interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { currentPath } = useRouter();

  const getPlatform = (path: string): 'youtube' | 'instagram' | 'generic' => {
    if (path.includes('youtube')) return 'youtube';
    if (path.includes('instagram')) return 'instagram';
    return 'generic';
  };

  const platform = getPlatform(currentPath);

  return (
    <PlatformThemeProvider platform={platform}>
      <a href="#main-content" className="skip-link">Skip to content</a>
      <Header />
      <DesktopSideGutterAds />
      <main className="site-main" id="main-content" tabIndex={-1}>
        {children}
      </main>
      <Footer />
    </PlatformThemeProvider>
  );
};
