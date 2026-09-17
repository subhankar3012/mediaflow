import React, { useState, useEffect, useRef } from 'react';

export interface AnimatedHeroTitleProps {
  phrases?: string[];
  typingSpeed?: number;
  deletingSpeed?: number;
  pauseDuration?: number;
  className?: string;
  fallbackTitle?: string;
}

const DEFAULT_PHRASES: string[] = [
  'Online Video & Audio Downloader',
  'YouTube Video Downloader',
  'YouTube to MP3 Converter',
  'Instagram Reels Downloader',
  'Instagram Video Downloader',
];

// Helper: computes organic human typing delay with natural micro-pauses, bursts, and word boundaries
function calculateHumanTypingDelay(
  currentLen: number,
  targetPhrase: string,
  baseSpeed: number,
  burstRef: React.MutableRefObject<number>
): number {
  const currentChar = targetPhrase[currentLen];
  const nextChar = targetPhrase[currentLen + 1] || '';

  // 1. Initial finger placement on first character
  if (currentLen === 0) {
    return baseSpeed + 80 + Math.random() * 40;
  }

  // 2. Shift key coordination for capital letters
  if (/[A-Z]/.test(currentChar) && currentLen > 0) {
    return baseSpeed + 65 + Math.random() * 45;
  }

  // 3. Special symbol '&' requires longer finger reach
  if (currentChar === '&') {
    return baseSpeed + 110 + Math.random() * 60;
  }

  // 4. Word boundary: spaces naturally incur a cognitive pause between words
  if (currentChar === ' ' || nextChar === ' ') {
    // 25% chance of a slightly deeper reflection pause after a word
    if (Math.random() < 0.25) {
      return baseSpeed + 190 + Math.random() * 110; // ~255ms - 365ms
    }
    return baseSpeed + 80 + Math.random() * 50; // ~145ms - 195ms
  }

  // 5. Fast typing burst (typing familiar letter clusters quickly: 2-4 chars)
  if (burstRef.current > 0) {
    burstRef.current--;
    return Math.max(32, baseSpeed - 28 + Math.random() * 16); // ~37ms - 53ms rapid
  }

  // 6. Occasional mid-word micro-hesitation (12% chance)
  if (Math.random() < 0.12) {
    burstRef.current = Math.floor(2 + Math.random() * 3);
    return baseSpeed + 120 + Math.random() * 75; // ~185ms - 260ms
  }

  // 7. Approaching phrase completion: gentle deceleration
  if (currentLen >= targetPhrase.length - 2) {
    return baseSpeed + 35 + Math.random() * 25;
  }

  // 8. Normal typing cadence with organic jitter
  if (Math.random() < 0.28) {
    burstRef.current = Math.floor(2 + Math.random() * 3);
  }
  return baseSpeed - 8 + Math.random() * 22; // ~57ms - 79ms
}

export const AnimatedHeroTitle: React.FC<AnimatedHeroTitleProps> = ({
  phrases = DEFAULT_PHRASES,
  typingSpeed = 65,
  deletingSpeed = 32,
  pauseDuration = 2300,
  className = '',
  fallbackTitle = 'Online Video & Audio Downloader',
}) => {
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [displayedText, setDisplayedText] = useState('');
  const [mode, setMode] = useState<
    'typing' | 'holding' | 'hesitating' | 'deleting' | 'paused'
  >('typing');
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    return false;
  });

  const timerRef = useRef<number | null>(null);
  const burstCountRef = useRef<number>(0);

  // Listen to prefers-reduced-motion changes
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    const handler = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  // Main organic animation loop
  useEffect(() => {
    if (prefersReducedMotion) {
      return;
    }

    const currentTarget = phrases[phraseIndex] || '';

    const clearActiveTimer = () => {
      if (timerRef.current !== null) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };

    clearActiveTimer();

    if (mode === 'typing') {
      if (displayedText.length < currentTarget.length) {
        const currentLen = displayedText.length;
        const delay = calculateHumanTypingDelay(
          currentLen,
          currentTarget,
          typingSpeed,
          burstCountRef
        );
        const nextLen = currentLen + 1;

        timerRef.current = window.setTimeout(() => {
          setDisplayedText(currentTarget.slice(0, nextLen));
          if (nextLen === currentTarget.length) {
            setMode('holding');
          }
        }, delay);
      }
    } else if (mode === 'holding') {
      // Varied reading pause on every loop: ~2100ms - 2800ms
      const readingDuration = pauseDuration - 200 + Math.random() * 700;

      timerRef.current = window.setTimeout(() => {
        // Natural hesitation before deletion starts
        setMode('hesitating');
      }, readingDuration);
    } else if (mode === 'hesitating') {
      // Brief human hesitation before backspacing starts (~280ms - 420ms)
      const hesitationDelay = 280 + Math.random() * 140;

      timerRef.current = window.setTimeout(() => {
        setMode('deleting');
      }, hesitationDelay);
    } else if (mode === 'deleting') {
      if (displayedText.length > 1) {
        // Variable deletion rhythm
        let delDelay = deletingSpeed;
        if (displayedText.length >= currentTarget.length - 2) {
          // Slower initial backspace keystrokes (~60ms - 80ms)
          delDelay = deletingSpeed + 35 + Math.random() * 15;
        } else if (Math.random() < 0.1) {
          // Occasional micro-stutter while deleting
          delDelay = deletingSpeed + 32 + Math.random() * 20;
        } else {
          // Rapid held backspace (~24ms - 38ms)
          delDelay = Math.max(22, deletingSpeed - 8 + Math.random() * 14);
        }

        timerRef.current = window.setTimeout(() => {
          setDisplayedText(currentTarget.slice(0, displayedText.length - 1));
        }, delDelay);
      } else if (displayedText.length === 1) {
        // Erasing final character
        const delDelay = deletingSpeed + 15 + Math.random() * 15;
        timerRef.current = window.setTimeout(() => {
          setDisplayedText('');
          setMode('paused');
          setIsTransitioning(true);
        }, delDelay);
      }
    } else if (mode === 'paused') {
      // Natural pause after deletion before starting next phrase (~280ms - 450ms)
      const interPhraseDelay = 300 + Math.random() * 160;

      timerRef.current = window.setTimeout(() => {
        setPhraseIndex((prev) => (prev + 1) % phrases.length);
        setIsTransitioning(false);
        burstCountRef.current = 0;
        setMode('typing');
      }, interPhraseDelay);
    }

    return () => {
      clearActiveTimer();
    };
  }, [
    displayedText,
    mode,
    phraseIndex,
    phrases,
    typingSpeed,
    deletingSpeed,
    pauseDuration,
    prefersReducedMotion,
  ]);

  const activePhrase = phrases[phraseIndex] || fallbackTitle;
  const isCaretIdle = mode === 'holding' || mode === 'hesitating' || mode === 'paused';

  return (
    <h1
      className={`hero-editorial-h1 ${className}`.trim()}
      aria-label={activePhrase}
    >
      {/* Accessible text for screen readers and SEO */}
      <span className="sr-only">{activePhrase}</span>

      {/* Visual zero-layout-shift headline container */}
      <span className="hero-animated-title-container" aria-hidden="true">
        {/* Ghost templates: render all candidate phrases in same grid cell to permanently lock dimensions */}
        {phrases.map((phrase, idx) => (
          <span key={idx} className="hero-title-ghost">
            {phrase}
            <span className="hero-title-cursor ghost" />
          </span>
        ))}

        {/* Active typed phrase with organic rhythm */}
        <span
          className={`hero-title-active ${isTransitioning ? 'transitioning' : ''}`}
        >
          <span className="hero-title-text">
            {prefersReducedMotion ? activePhrase : (displayedText || '\u200B')}
          </span>
          {!prefersReducedMotion && (
            <span
              className={`hero-title-cursor ${isCaretIdle ? 'blinking' : 'typing'}`}
            />
          )}
        </span>
      </span>
    </h1>
  );
};
