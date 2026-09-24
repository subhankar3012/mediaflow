import React, { useState, useEffect, useRef, memo } from 'react';
import { appConfig } from '../../config/appConfig';

export interface AdsterraBannerProps {
  slotType?:
    | 'top'
    | 'between'
    | 'bottom'
    | 'rectangle'
    | 'banner468'
    | 'processing'
    | 'native'
    | 'inline'
    | 'skyscraper'
    | 'skyscraper-left'
    | 'skyscraper-right'
    | 'skyscraper160x600'
    | 'skyscraper160x300'
    | string;
  className?: string;
  slotId?: string;
  hideLabel?: boolean;
}

export const AdsterraBanner: React.FC<AdsterraBannerProps> = memo(({
  slotType = 'top',
  className = '',
  slotId,
  hideLabel = false,
}) => {
  const [isMobile, setIsMobile] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const writtenKeyRef = useRef<string>('');

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

  // Determine key, dimensions, and type based on slotType & device
  let key = '';
  let width = 300;
  let height = 250;
  let isNative = false;

  if (slotType === 'native') {
    isNative = true;
    width = 320;
    height = 180;
  } else if (slotType === 'processing') {
    // High-engagement Medium Rectangle (300x250) during progress/conversion
    key = appConfig.adsterraBanners.rectangle300x250;
    width = 300;
    height = 250;
  } else if (slotType === 'banner468') {
    // 468x60 on desktop, 320x50 on mobile
    key = isMobile ? appConfig.adsterraBanners.mobile320x50 : appConfig.adsterraBanners.banner468x60;
    width = isMobile ? 320 : 468;
    height = isMobile ? 50 : 60;
  } else if (slotType === 'rectangle') {
    // 300x250 Medium Rectangle
    key = appConfig.adsterraBanners.rectangle300x250;
    width = 300;
    height = 250;
  } else if (slotType === 'between') {
    // Distinct slot: 468x60 on desktop, 320x50 on mobile
    key = isMobile ? appConfig.adsterraBanners.mobile320x50 : appConfig.adsterraBanners.banner468x60;
    width = isMobile ? 320 : 468;
    height = isMobile ? 50 : 60;
  } else if (slotType === 'skyscraper-left' || slotType === 'skyscraper160x600') {
    key = appConfig.adsterraBanners.skyscraper160x600 || '75d42770ad9b0b3039cf57a7e55e9e62';
    width = 160;
    height = 600;
  } else if (slotType === 'skyscraper-right' || slotType === 'skyscraper160x300') {
    key = appConfig.adsterraBanners.skyscraper160x300 || '2dc4ff74d0f64b72e28e643c3d1676d8';
    width = 160;
    height = 300;
  } else if (slotType === 'skyscraper') {
    key = appConfig.adsterraBanners.skyscraper160x600 || appConfig.adsterraBanners.skyscraper160x300;
    width = 160;
    height = 600;
  } else if (slotType === 'bottom') {
    // Bottom slot: Leaderboard 728x90 on desktop, 320x50 on mobile
    key = isMobile ? appConfig.adsterraBanners.mobile320x50 : appConfig.adsterraBanners.leaderboard728x90;
    width = isMobile ? 320 : 728;
    height = isMobile ? 50 : 90;
  } else {
    // Default top: 728x90 on desktop, 320x50 on mobile
    key = isMobile ? appConfig.adsterraBanners.mobile320x50 : appConfig.adsterraBanners.leaderboard728x90;
    width = isMobile ? 320 : 728;
    height = isMobile ? 50 : 90;
  }

  // Construct iframe document HTML
  const iframeHtml = isNative
    ? `<!DOCTYPE html>
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
</html>`
    : `<!DOCTYPE html>
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
</html>`;

  // Safely inject into iframe via doc.write to inherit real domain origin without about:srcdoc blanking
  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;

    const currentKey = `${key}-${width}x${height}-${isNative ? 'nat' : 'std'}`;
    if (writtenKeyRef.current === currentKey) return;

    const writeDoc = () => {
      try {
        const doc = iframe.contentDocument || iframe.contentWindow?.document;
        if (doc) {
          doc.open();
          doc.write(iframeHtml);
          doc.close();
          writtenKeyRef.current = currentKey;
        }
      } catch (err) {
        console.warn('Adsterra iframe write error:', err);
      }
    };

    if (iframe.contentDocument) {
      writeDoc();
    } else {
      iframe.onload = writeDoc;
    }
  }, [iframeHtml, key, width, height, isNative]);

  const frameWidth = isNative ? '100%' : width;
  const frameHeight = isNative ? 180 : height;

  return (
    <aside
      id={slotId}
      className={`adsterra-slot adsterra-${slotType} ${className}`.trim()}
      role="complementary"
      aria-label="Sponsored Content"
      style={{
        width: '100%',
        margin: slotType.includes('skyscraper') ? '0 auto' : slotType === 'processing' ? '0.75rem auto 0.25rem auto' : '1.5rem auto',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {!hideLabel && (
        <div
          style={{
            fontSize: '0.625rem',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: 'var(--slate-400)',
            marginBottom: '4px',
            fontFamily: 'var(--font-mono)',
            textAlign: 'center',
            userSelect: 'none',
          }}
        >
          {isNative ? 'Sponsored Recommendations' : 'Advertisement'}
        </div>
      )}
      <iframe
        ref={iframeRef}
        title={`Adsterra ${slotType} Ad`}
        width={frameWidth}
        height={frameHeight}
        style={{
          border: 'none',
          maxWidth: '100%',
          overflow: 'hidden',
          display: 'block',
          minHeight: `${frameHeight}px`,
        }}
        scrolling="no"
      />
    </aside>
  );
});
