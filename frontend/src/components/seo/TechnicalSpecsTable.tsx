import React from 'react';

export interface SpecRow {
  feature: string;
  mp4Detail: string;
  mp3Detail: string;
  deviceSupport: string;
}

export interface TechnicalSpecsTableProps {
  platform?: 'youtube' | 'instagram' | 'all';
  title?: string;
  description?: string;
}

export const TechnicalSpecsTable: React.FC<TechnicalSpecsTableProps> = ({
  platform = 'all',
  title = 'Technical Specifications & Format Details',
  description = 'MediaFlow automatically detects, processes, and remuxes streams to match universal media playback standards across all modern operating systems.',
}) => {
  const isInstagram = platform === 'instagram';

  const rows: SpecRow[] = isInstagram
    ? [
        {
          feature: 'Container Format',
          mp4Detail: 'MP4 (MPEG-4 Part 14)',
          mp3Detail: 'MP3 / AAC Audio',
          deviceSupport: 'Universal (iOS, Android, Windows, Mac)',
        },
        {
          feature: 'Video Codec',
          mp4Detail: 'H.264 / AVC (High Profile)',
          mp3Detail: 'N/A (Extracted Soundtrack)',
          deviceSupport: 'Native hardware playback on all GPUs',
        },
        {
          feature: 'Audio Codec & Bitrate',
          mp4Detail: 'AAC Stereo @ up to 256 kbps',
          mp3Detail: 'MP3 Stereo @ 128–320 kbps',
          deviceSupport: 'All music players, cars & DAWs',
        },
        {
          feature: 'Resolution & Aspect Ratio',
          mp4Detail: '1080x1920 (9:16 Reels) / 1080x1080',
          mp3Detail: 'N/A',
          deviceSupport: 'Vertical mobile screens & desktop',
        },
        {
          feature: 'Watermark Policy',
          mp4Detail: '100% Clean — No Watermark Added',
          mp3Detail: 'Original sound without voiceover cuts',
          deviceSupport: 'Direct offline archive & sharing',
        },
      ]
    : [
        {
          feature: 'Container Format',
          mp4Detail: 'MP4 (MPEG-4 Part 14)',
          mp3Detail: 'MP3 (MPEG-1 Audio Layer III)',
          deviceSupport: 'Universal (iOS, Android, Windows, Mac, Smart TVs)',
        },
        {
          feature: 'Video Codec & Encoding',
          mp4Detail: 'H.264 / AVC (Standard Progressive)',
          mp3Detail: 'N/A (Audio Stream)',
          deviceSupport: 'Zero transcoding lag on any device',
        },
        {
          feature: 'Max Video Resolution',
          mp4Detail: '1080p FHD (1920x1080), 720p HD, 360p',
          mp3Detail: 'N/A (Audio Track Only)',
          deviceSupport: 'Retina, 4K monitors, and mobile displays',
        },
        {
          feature: 'Audio Fidelity & Bitrate',
          mp4Detail: 'AAC-LC Stereo @ 128–192 kbps',
          mp3Detail: 'Constant Bitrate (CBR) up to 320 kbps',
          deviceSupport: 'Hi-Fi headphones, car audio, Apple Music, VLC',
        },
        {
          feature: 'Stream Muxing (FFmpeg)',
          mp4Detail: 'Auto-muxed video + audio streams',
          mp3Detail: 'Clean loss-minimized audio extraction',
          deviceSupport: 'Guarantees synchronized sound on 1080p',
        },
      ];

  return (
    <section className="specs-section site-container">
      <div className="section-header text-center">
        <h2 className="section-h2">{title}</h2>
        <p className="section-sub">{description}</p>
      </div>

      <div className="specs-table-wrapper">
        <table className="specs-table">
          <thead>
            <tr>
              <th scope="col">Specification</th>
              <th scope="col">Video (MP4)</th>
              <th scope="col">Audio (MP3)</th>
              <th scope="col">Compatibility & Playback</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.feature}>
                <td className="specs-feature-name">
                  <strong>{row.feature}</strong>
                </td>
                <td className="specs-cell-mono">{row.mp4Detail}</td>
                <td className="specs-cell-mono">{row.mp3Detail}</td>
                <td className="specs-cell-desc">{row.deviceSupport}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};
