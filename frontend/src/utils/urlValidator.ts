/**
 * Validates and normalizes URLs supported by the MediaFlow downloader.
 * Supported platforms: YouTube and Instagram.
 * Supports clean URLs, mobile shortlinks (youtu.be), and URLs shared with caption text from mobile apps.
 */

/**
 * Extracts a supported YouTube or Instagram URL from raw input, including mobile share captions.
 */
export function extractSupportedUrl(input: string): string | null {
  if (!input) return null;
  const text = input.trim();
  if (!text) return null;

  // 1. Direct regex match for YouTube or Instagram URLs (with or without protocol)
  const match = text.match(
    /(?:https?:\/\/)?(?:[a-zA-Z0-9-]+\.)?(?:youtube\.com|youtu\.be|instagram\.com)\/[^\s]+/i
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
      // Must have some path or video identifier (watch?v=..., /shorts/..., /live/..., /ID)
      return parsed.pathname.length > 1 || parsed.search.length > 1;
    }

    // Instagram checks
    if (
      host === 'instagram.com' ||
      host.endsWith('.instagram.com')
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
    if (
      text.startsWith('youtube.com') ||
      text.startsWith('www.youtube.com') ||
      text.startsWith('m.youtube.com') ||
      text.startsWith('youtu.be') ||
      text.startsWith('instagram.com') ||
      text.startsWith('www.instagram.com')
    ) {
      return `https://${text}`;
    }
  }
  return text;
}

