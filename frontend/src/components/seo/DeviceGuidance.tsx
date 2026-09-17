import React from 'react';

export const DeviceGuidance: React.FC = () => {
  return (
    <section className="device-guidance-section site-container">
      <div className="section-header text-center">
        <h2 className="section-h2">How to Save Media on Any Device</h2>
        <p className="section-sub">
          MediaFlow runs directly in any modern web browser without requiring third-party companion apps or jailbreaks.
        </p>
      </div>

      <div className="device-guidance-grid">
        {/* Windows & Mac Desktop */}
        <div className="device-card">
          <div className="device-card-header">
            <span className="device-badge">PC & Mac</span>
            <h3 className="device-card-title">Windows, macOS & Linux</h3>
          </div>
          <p className="device-card-desc">
            Use any standard desktop browser (Google Chrome, Firefox, Safari, Microsoft Edge, or Brave).
          </p>
          <ul className="device-step-list">
            <li>
              <strong>1. Paste & Click Search:</strong> Paste the copied video link into the search bar.
            </li>
            <li>
              <strong>2. Select Format:</strong> Choose MP4 (up to 1080p) or MP3 audio.
            </li>
            <li>
              <strong>3. Save to Downloads:</strong> Click &ldquo;Download&rdquo;. Your browser will automatically save the file directly to your system&rsquo;s <code>Downloads</code> folder.
            </li>
          </ul>
        </div>

        {/* Android Phones & Tablets */}
        <div className="device-card">
          <div className="device-card-header">
            <span className="device-badge">Android</span>
            <h3 className="device-card-title">Android Smartphones & Tablets</h3>
          </div>
          <p className="device-card-desc">
            Optimized for Chrome, Samsung Internet, and Firefox on all modern Android versions.
          </p>
          <ul className="device-step-list">
            <li>
              <strong>1. Copy from App:</strong> In the YouTube or Instagram app, tap &ldquo;Share&rdquo; &rarr; &ldquo;Copy Link&rdquo;.
            </li>
            <li>
              <strong>2. Automatic Detection:</strong> Open MediaFlow and click &ldquo;Paste Link&rdquo; or paste into the box.
            </li>
            <li>
              <strong>3. Open via Files:</strong> Once the download finishes, swipe down your notification tray or open the <em>Files by Google</em> app to view or play your media.
            </li>
          </ul>
        </div>

        {/* iPhone & iPad (iOS Safari) */}
        <div className="device-card">
          <div className="device-card-header">
            <span className="device-badge">Apple iOS</span>
            <h3 className="device-card-title">iPhone & iPad (iOS Safari)</h3>
          </div>
          <p className="device-card-desc">
            Apple iOS 13+ supports direct browser downloads via native Safari download management.
          </p>
          <ul className="device-step-list">
            <li>
              <strong>1. Open in Safari:</strong> Copy your media link and open MediaFlow in Apple Safari.
            </li>
            <li>
              <strong>2. Tap Download:</strong> Select your quality and tap &ldquo;Download MP4&rdquo; or &ldquo;Download MP3&rdquo;. Confirm the Safari download prompt.
            </li>
            <li>
              <strong>3. Save to Photos/Files:</strong> Tap the blue circle download icon in Safari&rsquo;s address bar, tap the file, and select &ldquo;Save Video&rdquo; to send it directly to your Photos camera roll.
            </li>
          </ul>
        </div>
      </div>
    </section>
  );
};
