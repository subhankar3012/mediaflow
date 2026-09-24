import React from 'react';
import { Link } from '../../router/Link';
import { appConfig } from '../../config/appConfig';

export const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="site-footer" role="contentinfo">
      <div className="site-container">
        {/* Main Footer Links Grid */}
        <div className="footer-grid">
          {/* Brand & Description */}
          <div className="footer-brand">
            <Link to="/" className="pill-brand" style={{ display: 'inline-flex', padding: 0 }}>
              <img
                src="/brand-icon.png"
                alt="MediaFlow Logo"
                className="pill-brand-img"
                width="28"
                height="28"
              />
              <span className="pill-brand-title" style={{ fontSize: '1.2rem' }}>
                Media<span className="pill-brand-flow">Flow</span>
              </span>
            </Link>
            <p>
              An understated, lightning-fast utility for YouTube and Instagram. Clean direct media extraction with zero loss.
            </p>
          </div>

          {/* YouTube Tools */}
          <div className="footer-col">
            <h4>YouTube Tools</h4>
            <ul>
              <li>
                <Link to="/youtube-video-downloader">YouTube Video Downloader</Link>
              </li>
              <li>
                <Link to="/youtube-to-mp3">YouTube to MP3 Converter</Link>
              </li>
              <li>
                <Link to="/youtube-to-mp4">YouTube to MP4 Downloader</Link>
              </li>
            </ul>
          </div>

          {/* Instagram Tools */}
          <div className="footer-col">
            <h4>Instagram Tools</h4>
            <ul>
              <li>
                <Link to="/instagram-downloader">Instagram Video Downloader</Link>
              </li>
              <li>
                <Link to="/instagram-reels-downloader">Instagram Reels Downloader</Link>
              </li>
            </ul>
          </div>

          {/* Company & Legal */}
          <div className="footer-col">
            <h4>Legal &amp; Info</h4>
            <ul>
              <li>
                <Link to="/faq">FAQ &amp; Guide</Link>
              </li>
              <li>
                <Link to="/about">About Us</Link>
              </li>
              <li>
                <Link to="/privacy-policy">Privacy Policy</Link>
              </li>
              <li>
                <Link to="/terms">Terms of Service</Link>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => {
                    const directLink = appConfig.monetagDirectLink || appConfig.adsterraDirectLink;
                    if (appConfig.enableAds && directLink) {
                      try {
                        window.open(directLink, '_blank', 'noopener,noreferrer');
                      } catch {}
                    }
                    window.dispatchEvent(new CustomEvent('mediaflow:open-app-modal'));
                  }}
                  style={{
                    background: 'none',
                    border: 'none',
                    padding: 0,
                    font: 'inherit',
                    color: '#10b981',
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontWeight: 600,
                  }}
                >
                  <span>📱 Download Android App</span>
                </button>
              </li>
              <li>
                <Link to="/contact">Contact Support</Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Minimal Bottom Bar */}
        <div className="footer-bottom">
          <div className="footer-bottom-brand">
            <span>© {currentYear} {appConfig.brandName}. Clean &amp; compliant media extraction.</span>
          </div>
          <div className="footer-bottom-links">
            <Link to="/terms">Terms</Link>
            <Link to="/privacy-policy">Privacy</Link>
            <Link to="/about">About</Link>
            <Link to="/contact" style={{ color: 'var(--platform-accent-text)', fontWeight: 600 }}>Contact</Link>
          </div>
        </div>
      </div>
    </footer>
  );
};
