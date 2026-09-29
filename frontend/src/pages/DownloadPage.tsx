import React, { useEffect, useState } from 'react';
import { HeadMeta } from '../components/seo/HeadMeta';

export const DownloadPage: React.FC = () => {
  const [downloadStarted, setDownloadStarted] = useState(false);
  const apkUrl = '/download/apk';
  const version = '1.5.9';

  useEffect(() => {
    // Automatically trigger APK download after 1.5 seconds on mobile
    const timer = setTimeout(() => {
      try {
        const link = document.createElement('a');
        link.href = apkUrl;
        link.setAttribute('download', 'MediaFlow-release.apk');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setDownloadStarted(true);
      } catch (_) {}
    }, 1500);

    return () => clearTimeout(timer);
  }, []);

  return (
    <>
      <HeadMeta
        title="Download MediaFlow for Android (Official APK • v1.5.9)"
        description="Download MediaFlow Android App for high-speed 4K/1080p video and photo downloads from YouTube, Instagram, X/Twitter, and Reddit."
        canonicalPath="/download"
      />

      <div style={{ maxWidth: '640px', margin: '40px auto', padding: '0 20px', textAlign: 'center' }}>
        <div
          style={{
            background: 'var(--color-bg-card, #0f172a)',
            border: '1px solid var(--color-border, #1e293b)',
            borderRadius: '24px',
            padding: '36px 24px',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4)',
          }}
        >
          {/* Logo Badge */}
          <div
            style={{
              width: '68px',
              height: '68px',
              margin: '0 auto 18px',
              background: 'linear-gradient(135deg, #e11d48, #f43f5e)',
              borderRadius: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '32px',
              boxShadow: '0 10px 25px rgba(225, 29, 72, 0.4)',
            }}
          >
            🚀
          </div>

          <h1 style={{ fontSize: '26px', fontWeight: '800', color: '#f8fafc', marginBottom: '8px' }}>
            MediaFlow for Android
          </h1>

          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <span
              style={{
                background: '#e11d48',
                color: '#ffffff',
                fontSize: '12px',
                fontWeight: '800',
                padding: '4px 10px',
                borderRadius: '8px',
              }}
            >
              v{version}
            </span>
            <span style={{ color: '#94a3b8', fontSize: '13px' }}>~115 MB • 100% On-Device Engine</span>
          </div>

          <p style={{ color: '#cbd5e1', fontSize: '15px', lineHeight: '1.6', marginBottom: '28px' }}>
            {downloadStarted
              ? 'Your APK download has started automatically! If it did not begin, tap the button below.'
              : 'Starting official APK download for your Android device...'}
          </p>

          {/* Primary Action Button */}
          <a
            href={apkUrl}
            download="MediaFlow-release.apk"
            onClick={() => setDownloadStarted(true)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              width: '100%',
              maxWidth: '360px',
              background: '#e11d48',
              color: '#ffffff',
              padding: '16px 28px',
              borderRadius: '14px',
              fontSize: '16px',
              fontWeight: '700',
              textDecoration: 'none',
              boxShadow: '0 8px 24px rgba(225, 29, 72, 0.35)',
              margin: '0 auto 24px',
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <span>{downloadStarted ? 'Download Again' : 'Download APK (v' + version + ')'}</span>
          </a>

          {/* 3 Step Installation Guide */}
          <div
            style={{
              background: 'rgba(255, 255, 255, 0.03)',
              borderRadius: '16px',
              padding: '20px',
              textAlign: 'left',
              border: '1px solid rgba(255, 255, 255, 0.06)',
            }}
          >
            <h3 style={{ fontSize: '14px', fontWeight: '700', color: '#e2e8f0', marginBottom: '12px' }}>
              Quick 3-Step Setup:
            </h3>
            <ol style={{ paddingLeft: '20px', margin: 0, color: '#94a3b8', fontSize: '13px', lineHeight: '1.8' }}>
              <li>
                Download the APK file onto your device (<strong style={{ color: '#f1f5f9' }}>MediaFlow-release.apk</strong>).
              </li>
              <li>
                Tap the completed download &rarr; If prompted, allow{' '}
                <em style={{ color: '#f1f5f9' }}>Settings &rarr; Allow from this source</em>.
              </li>
              <li>
                Tap <strong style={{ color: '#f1f5f9' }}>Install</strong>, open MediaFlow, and enjoy unlimited 4K downloads!
              </li>
            </ol>
          </div>

          <div style={{ marginTop: '24px' }}>
            <a
              href="/"
              style={{
                color: '#64748b',
                fontSize: '13px',
                textDecoration: 'none',
                fontWeight: '600',
              }}
            >
              &larr; Back to Web Downloader
            </a>
          </div>
        </div>
      </div>
    </>
  );
};
