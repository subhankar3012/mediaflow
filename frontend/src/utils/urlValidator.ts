/**
 * Validates and normalizes URLs supported by the MediaFlow downloader.
 * Supported platforms: YouTube, Instagram, X (Twitter), Facebook, Pinterest, Reddit.
 * Supports clean URLs, mobile shortlinks (youtu.be, fb.watch, pin.it, redd.it),
 * and URLs shared with caption text from mobile apps.
 */

/**
 * Extracts a supported URL from raw input, including mobile share captions.
 */
export function extractSupportedUrl(input: string): string | null {
  if (!input) return null;
  const text = input.trim();
  if (!text) return null;

  // 1. Direct regex match for supported platform URLs (with or without protocol)
  const match = text.match(
    /(?:https?:\/\/)?(?:[a-zA-Z0-9-]+\.)?(?:youtube\.com|youtu\.be|instagram\.com|x\.com|twitter\.com|facebook\.com|fb\.watch|pinterest\.com|pin\.it|reddit\.com|redd\.it)\/[^\s]+/i
  );
  if (match) {
    let extracted = match[0];
    // Clean trailing punctuation often attached from sentences (e.g. 'youtu.be/xyz.')
    extracted = extracted.replace(/[.,;!?)]+$/, '');
    if (!/^https?:\/\//i.test(extracted)) {
      extracted = `https://${extracted}`;
    }
    return extracted;
  }

  return null;
}

export function isValidSupportedUrl(input: string): boolean {
  if (!input) return false;
  const text = input.trim();
  if (!text) return false;

  const candidate = extractSupportedUrl(text);
  if (!candidate) return false;

  try {
    const parsed = new URL(candidate);
    const host = parsed.hostname.toLowerCase();

    // YouTube checks
    if (
      host === 'youtu.be' ||
      host === 'youtube.com' ||
      host.endsWith('.youtube.com')
    ) {
      return parsed.pathname.length > 1 || parsed.search.length > 1;
    }

    // Instagram checks
    if (
      host === 'instagram.com' ||
      host.endsWith('.instagram.com')
    ) {
      return parsed.pathname.length > 1;
    }

    // X / Twitter checks
    if (
      host === 'x.com' ||
      host.endsWith('.x.com') ||
      host === 'twitter.com' ||
      host.endsWith('.twitter.com')
    ) {
      return parsed.pathname.length > 1;
    }

    // Facebook checks
    if (
      host === 'facebook.com' ||
      host.endsWith('.facebook.com') ||
      host === 'fb.watch' ||
      host.endsWith('.fb.watch')
    ) {
      return parsed.pathname.length > 1 || parsed.search.length > 1;
    }

    // Pinterest checks
    if (
      host === 'pinterest.com' ||
      host.endsWith('.pinterest.com') ||
      host === 'pin.it' ||
      host.endsWith('.pin.it')
    ) {
      return parsed.pathname.length > 1;
    }

    // Reddit checks
    if (
      host === 'reddit.com' ||
      host.endsWith('.reddit.com') ||
      host === 'redd.it' ||
      host.endsWith('.redd.it')
    ) {
      return parsed.pathname.length > 1;
    }
  } catch {
    return false;
  }

  return false;
}

export function normalizeInputUrl(input: string): string {
  if (!input) return '';
  const text = input.trim();
  if (!text) return '';

  const extracted = extractSupportedUrl(text);
  if (extracted) {
    return extracted;
  }

  if (!/^https?:\/\//i.test(text)) {
    const candidateLower = text.toLowerCase();
    const knownHosts = [
      'youtube.com',
      'www.youtube.com',
      'm.youtube.com',
      'youtu.be',
      'instagram.com',
      'www.instagram.com',
      'x.com',
      'www.x.com',
      'twitter.com',
      'www.twitter.com',
      'mobile.twitter.com',
      'facebook.com',
      'www.facebook.com',
      'm.facebook.com',
      'fb.watch',
      'pinterest.com',
      'www.pinterest.com',
      'pin.it',
      'reddit.com',
      'www.reddit.com',
      'old.reddit.com',
      'redd.it',
      'v.redd.it',
    ];

    if (knownHosts.some((h) => candidateLower.startsWith(h))) {
      return `https://${text}`;
    }
  }
  return text;
}
