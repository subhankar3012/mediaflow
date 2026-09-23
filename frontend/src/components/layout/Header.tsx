import React, { useState, useRef, useEffect } from 'react';
import { Link } from '../../router/Link';
import { useRouter } from '../../router/Router';
import { appConfig } from '../../config/appConfig';
import { AppBanner } from './AppBanner';
import { AppDownloadModal } from './AppDownloadModal';

const TOOL_ROUTES = [
  { path: '/youtube-video-downloader', label: 'YouTube Video Downloader', badge: '1080p / 4K' },
  { path: '/youtube-to-mp3', label: 'YouTube to MP3', badge: '320kbps' },
  { path: '/youtube-to-mp4', label: 'YouTube to MP4', badge: 'Fast MP4' },
  { path: '/instagram-downloader', label: 'Instagram Video', badge: 'Direct CDN' },
  { path: '/instagram-reels-downloader', label: 'Instagram Reels', badge: 'Vertical HD' },
];

export const Header: React.FC = () => {
  const { currentPath } = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [toolsDropdownOpen, setToolsDropdownOpen] = useState(false);
  const [appModalOpen, setAppModalOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOpenAppModal = () => setAppModalOpen(true);
    window.addEventListener('mediaflow:open-app-modal', handleOpenAppModal);
    return () => window.removeEventListener('mediaflow:open-app-modal', handleOpenAppModal);
  }, []);

  const isToolActive = TOOL_ROUTES.some((tool) => tool.path === currentPath);

  const toggleMobileMenu = () => {
    setMobileMenuOpen((prev) => !prev);
    setToolsDropdownOpen(false);
  };

  const closeAllMenus = () => {
    setMobileMenuOpen(false);
    setToolsDropdownOpen(false);
  };

  const handleQuickPaste = async () => {
    closeAllMenus();
    let clipboardText = '';
    try {
      if (navigator.clipboard && navigator.clipboard.readText) {
        clipboardText = await navigator.clipboard.readText();
      }
    } catch {
      // Permission denied or not available; fallback to focusing input
    }

    if (clipboardText && clipboardText.trim()) {
      window.dispatchEvent(
        new CustomEvent('mediaflow:paste-url', {
          detail: { text: clipboardText.trim() },
        })
      );
    } else {
      const isMobile =
        typeof window !== 'undefined' &&
        (/Android|iPhone|iPad|iPod/i.test(navigator.userAgent) || window.innerWidth < 768);

      window.dispatchEvent(
        new CustomEvent('mediaflow:paste-hint', {
          detail: {
            hint: isMobile
              ? 'Tap & hold the box, then tap Paste (or tap clipboard above keyboard)'
              : 'Paste your link here (Ctrl+V / Cmd+V)',
          },
        })
      );
    }

    const input = document.getElementById('media-url-input') as HTMLInputElement | null;
    if (input) {
      input.focus();
      input.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setToolsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setToolsDropdownOpen(false);
        setMobileMenuOpen(false);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <header className="pill-header-wrapper" role="banner">
      {/* Top Announcement Strip for Android App */}
      <AppBanner onOpenModal={() => setAppModalOpen(true)} />

      <div className="pill-navbar">
        {/* Brand Wordmark */}
        <Link
          to="/"
          className="pill-brand"
          onClick={closeAllMenus}
          aria-label={`${appConfig.brandName} Home`}
        >
          <img
            src="/brand-icon.png"
            alt="MediaFlow Logo"
            className="pill-brand-img"
            width="26"
            height="26"
          />
          <span className="pill-brand-title">
            Media<span className="pill-brand-flow">Flow</span>
          </span>
        </Link>

        {/* Clean Desktop Navigation Links */}
        <nav className="pill-desktop-nav" role="navigation" aria-label="Main Navigation">
          <Link
            to="/youtube-video-downloader"
            className={`pill-nav-link ${currentPath === '/youtube-video-downloader' || currentPath === '/' ? 'active' : ''}`}
            onClick={closeAllMenus}
          >
            Downloader
          </Link>
          <Link
            to="/youtube-to-mp3"
            className={`pill-nav-link ${currentPath === '/youtube-to-mp3' ? 'active' : ''}`}
            onClick={closeAllMenus}
          >
            MP3 Converter
          </Link>
          <Link
            to="/instagram-reels-downloader"
            className={`pill-nav-link ${currentPath === '/instagram-reels-downloader' ? 'active' : ''}`}
            onClick={closeAllMenus}
          >
            Reels &amp; Shorts
          </Link>

          {/* Tools Dropdown */}
          <div className="pill-dropdown-wrapper" ref={dropdownRef}>
            <button
              type="button"
              className={`pill-nav-link pill-dropdown-trigger ${isToolActive ? 'active' : ''}`}
              onClick={() => setToolsDropdownOpen((prev) => !prev)}
              aria-expanded={toolsDropdownOpen}
              aria-haspopup="true"
            >
              <span>More Tools</span>
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{
                  transform: toolsDropdownOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform var(--transition-fast)',
                }}
                aria-hidden="true"
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>

            {toolsDropdownOpen && (
              <div className="pill-dropdown-menu" role="menu">
                {TOOL_ROUTES.map((tool) => (
                  <Link
                    key={tool.path}
                    to={tool.path}
                    className={`pill-dropdown-item ${currentPath === tool.path ? 'active' : ''}`}
                    onClick={closeAllMenus}
                    role="menuitem"
                  >
                    <span className="dropdown-item-title">{tool.label}</span>
                    <span className="dropdown-item-badge">{tool.badge}</span>
                  </Link>
                ))}
              </div>
            )}
          </div>

          <a
            href="#how-it-works"
            className="pill-nav-link"
            onClick={closeAllMenus}
          >
            Guide
          </a>
          <Link
            to="/faq"
            className={`pill-nav-link ${currentPath === '/faq' ? 'active' : ''}`}
            onClick={closeAllMenus}
          >
            FAQ
          </Link>
        </nav>

        {/* Trailing Actions */}
        <div className="pill-actions">
          {/* Android App Button */}
          <button
            type="button"
            className="pill-app-btn"
            onClick={() => setAppModalOpen(true)}
            title="Download MediaFlow Android App (4K / 2K Ultra HD)"
            aria-label="Download MediaFlow Android App"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M17.523 15.3414c-.5511 0-.9993-.4486-.9993-.9997s.4482-.9993.9993-.9993c.551 0 .9993.4482.9993.9993 0 .5511-.4483.9997-.9993.9997m-11.046 0c-.5511 0-.9993-.4486-.9993-.9997s.4482-.9993.9993-.9993c.5511 0 .9993.4482.9993.9993 0 .5511-.4482.9997-.9993.9997m11.4045-6.02l1.9973-3.4592a.416.416 0 00-.1523-.5676.416.416 0 00-.5676.1523l-2.0223 3.503C15.5902 8.4116 13.8533 8 12 8s-3.5902.4116-5.1369.9499L4.8408 5.4469a.416.416 0 00-.5676-.1523.416.416 0 00-.1523.5676l1.9973 3.4592C2.6889 11.1867.3432 14.6589 0 18.761h24c-.3432-4.1021-2.6889-7.5743-6.1185-9.4396" />
            </svg>
            <span className="pill-app-btn-text">Android App</span>
          </button>

          <button
            type="button"
            className="pill-paste-btn"
            onClick={handleQuickPaste}
            title="Paste link from clipboard"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
            <span>Paste Link</span>
          </button>

          {/* Mobile Menu Toggle Button */}
          <button
            type="button"
            className="pill-mobile-toggle"
            onClick={toggleMobileMenu}
            aria-expanded={mobileMenuOpen}
            aria-label="Toggle navigation menu"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              {mobileMenuOpen ? (
                <>
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </>
              ) : (
                <>
                  <line x1="3" y1="12" x2="21" y2="12" />
                  <line x1="3" y1="6" x2="21" y2="6" />
                  <line x1="3" y1="18" x2="21" y2="18" />
                </>
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="pill-mobile-drawer">
          <button
            type="button"
            className="mobile-drawer-paste-btn"
            onClick={handleQuickPaste}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
            <span>Paste &amp; Analyze Link</span>
          </button>

          {/* Android App Button in Drawer */}
          <button
            type="button"
            className="mobile-drawer-link"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              color: '#059669',
              fontWeight: 600,
              background: 'rgba(16, 185, 129, 0.08)',
              borderRadius: '8px',
              padding: '10px 14px',
              margin: '6px 0',
              border: '1px solid rgba(16, 185, 129, 0.2)',
              width: '100%',
              textAlign: 'left',
              cursor: 'pointer',
            }}
            onClick={() => {
              closeAllMenus();
              setAppModalOpen(true);
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M17.523 15.3414c-.5511 0-.9993-.4486-.9993-.9997s.4482-.9993.9993-.9993c.551 0 .9993.4482.9993.9993 0 .5511-.4483.9997-.9993.9997m-11.046 0c-.5511 0-.9993-.4486-.9993-.9997s.4482-.9993.9993-.9993c.5511 0 .9993.4482.9993.9993 0 .5511-.4482.9997-.9993.9997m11.4045-6.02l1.9973-3.4592a.416.416 0 00-.1523-.5676.416.416 0 00-.5676.1523l-2.0223 3.503C15.5902 8.4116 13.8533 8 12 8s-3.5902.4116-5.1369.9499L4.8408 5.4469a.416.416 0 00-.5676-.1523.416.416 0 00-.1523.5676l1.9973 3.4592C2.6889 11.1867.3432 14.6589 0 18.761h24c-.3432-4.1021-2.6889-7.5743-6.1185-9.4396" />
            </svg>
            <span>Download Android App (4K / 2K)</span>
          </button>

          <div className="mobile-drawer-divider" />
          <Link
            to="/youtube-video-downloader"
            className={`mobile-drawer-link ${currentPath === '/youtube-video-downloader' || currentPath === '/' ? 'active' : ''}`}
            onClick={closeAllMenus}
          >
            YouTube Video Downloader
          </Link>
          <Link
            to="/youtube-to-mp3"
            className={`mobile-drawer-link ${currentPath === '/youtube-to-mp3' ? 'active' : ''}`}
            onClick={closeAllMenus}
          >
            YouTube to MP3 Converter
          </Link>
          <Link
            to="/youtube-to-mp4"
            className={`mobile-drawer-link ${currentPath === '/youtube-to-mp4' ? 'active' : ''}`}
            onClick={closeAllMenus}
          >
            YouTube to MP4 Downloader
          </Link>
          <Link
            to="/instagram-downloader"
            className={`mobile-drawer-link ${currentPath === '/instagram-downloader' ? 'active' : ''}`}
            onClick={closeAllMenus}
          >
            Instagram Video Downloader
          </Link>
          <Link
            to="/instagram-reels-downloader"
            className={`mobile-drawer-link ${currentPath === '/instagram-reels-downloader' ? 'active' : ''}`}
            onClick={closeAllMenus}
          >
            Instagram Reels Downloader
          </Link>
          <div className="mobile-drawer-divider" />
          <Link
            to="/faq"
            className={`mobile-drawer-link ${currentPath === '/faq' ? 'active' : ''}`}
            onClick={closeAllMenus}
          >
            FAQ &amp; Guide
          </Link>
          <Link
            to="/about"
            className={`mobile-drawer-link ${currentPath === '/about' ? 'active' : ''}`}
            onClick={closeAllMenus}
          >
            About
          </Link>
        </div>
      )}

      {/* App Download Modal */}
      <AppDownloadModal
        isOpen={appModalOpen}
        onClose={() => setAppModalOpen(false)}
      />
    </header>
  );
};

