import React, { useState, useEffect } from 'react';
import { appConfig } from '../../config/appConfig';

export interface AdsterraBannerProps {
  slotType?: 'top' | 'between' | 'bottom' | 'rectangle' | 'native' | string;
  className?: string;
  slotId?: string;
}

export const AdsterraBanner: React.FC<AdsterraBannerProps> = ({
  slotType = 'top',
  className = '',
  slotId,
}) => {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  if (!appConfig.enableAds) {
    return null;
  }

  // 1. Native Banner format for 'bottom' or 'native'
  if (slotType === 'bottom' || slotType === 'native') {
    const nativeHtml = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <base target="_blank">
          <style>
            html, body {
              margin: 0;
              padding: 0;
              background: transparent;
              width: 100%;
              overflow: hidden;
              font-family: system-ui, -apple-system, sans-serif;
            }
          </style>
        </head>
        <body>
          <div id="${appConfig.adsterraBanners.nativeContainerId}"></div>
          <script async="async" data-cfasync="false" src="${appConfig.adsterraBanners.nativeScriptSrc}"></script>
        </body>
      </html>
    `;

    return (
      <aside
        id={slotId}
        className={`adsterra-slot adsterra-native ${className}`.trim()}
        role="complementary"
        aria-label="Sponsored Content"
        style={{ width: '100%', margin: '1.5rem auto', textAlign: 'center' }}
      >
        <div style={{ fontSize: '0.625rem', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--slate-400)', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>
          Sponsored Recommendations
        </div>
        <iframe
          title="Adsterra Native Ad"
          srcDoc={nativeHtml}
          width="100%"
          height="160"
          style={{ border: 'none', maxWidth: '100%', minHeight: '150px', overflow: 'hidden' }}
          scrolling="no"
        />
      </aside>
    );
  }

  // 2. Medium Rectangle (300x250) for 'between' or 'rectangle'
  if (slotType === 'between' || slotType === 'rectangle') {
    const key = appConfig.adsterraBanners.rectangle300x250;
    const width = 300;
    const height = 250;

    const iframeHtml = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <base target="_blank">
          <style>
            html, body {
              margin: 0;
              padding: 0;
              width: 100%;
              height: 100%;
              display: flex;
              align-items: center;
              justify-content: center;
              background: transparent;
              overflow: hidden;
            }
          </style>
        </head>
        <body>
          <script type="text/javascript">
            atOptions = {
              'key' : '${key}',
              'format' : 'iframe',
              'height' : ${height},
              'width' : ${width},
              'params' : {}
            };
          </script>
          <script type="text/javascript" src="https://www.highrevenueformat.com/${key}/invoke.js"></script>
        </body>
      </html>
    `;

    return (
      <aside
        id={slotId}
        className={`adsterra-slot adsterra-rectangle ${className}`.trim()}
        role="complementary"
        aria-label="Advertisement"
        style={{ width: '100%', margin: '1.5rem auto', display: 'flex', flexDirection: 'column', alignItems: 'center' }}
      >
        <div style={{ fontSize: '0.625rem', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--slate-400)', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>
          Advertisement
        </div>
        <iframe
          title="Adsterra 300x250 Banner"
          srcDoc={iframeHtml}
          width={width}
          height={height}
          style={{ border: 'none', maxWidth: '100%', overflow: 'hidden' }}
          scrolling="no"
        />
      </aside>
    );
  }

  // 3. Top / Header Banner (728x90 on Desktop, 320x50 on Mobile)
  const key = isMobile
    ? appConfig.adsterraBanners.mobile320x50
    : appConfig.adsterraBanners.leaderboard728x90;
  const width = isMobile ? 320 : 728;
  const height = isMobile ? 50 : 90;

  const iframeHtml = `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <base target="_blank">
        <style>
          html, body {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: transparent;
            overflow: hidden;
          }
        </style>
      </head>
      <body>
        <script type="text/javascript">
          atOptions = {
            'key' : '${key}',
            'format' : 'iframe',
            'height' : ${height},
            'width' : ${width},
            'params' : {}
          };
        </script>
        <script type="text/javascript" src="https://www.highrevenueformat.com/${key}/invoke.js"></script>
      </body>
    </html>
  `;

  return (
    <aside
      id={slotId}
      className={`adsterra-slot adsterra-leaderboard ${className}`.trim()}
      role="complementary"
      aria-label="Advertisement"
      style={{ width: '100%', margin: '1.25rem auto', display: 'flex', flexDirection: 'column', alignItems: 'center' }}
    >
      <div style={{ fontSize: '0.625rem', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--slate-400)', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>
        Advertisement
      </div>
      <iframe
        title={`Adsterra ${width}x${height} Banner`}
        srcDoc={iframeHtml}
        width={width}
        height={height}
        style={{ border: 'none', maxWidth: '100%', overflow: 'hidden' }}
        scrolling="no"
      />
    </aside>
  );
};
