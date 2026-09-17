import React, { useState, useEffect, useRef } from 'react';
import { isValidSupportedUrl, normalizeInputUrl } from '../../utils/urlValidator';

export interface URLInputProps {
  url: string;
  onChange: (url: string) => void;
  onSubmit: (url: string) => void;
  loading: boolean;
  placeholder?: string;
  error?: string | null;
}

export const URLInput: React.FC<URLInputProps> = ({
  url,
  onChange,
  onSubmit,
  loading,
  placeholder = 'Paste YouTube or Instagram link here...',
  error,
}) => {
  const [localError, setLocalError] = useState<string | null>(null);
  const [hint, setHint] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const lastSearchedUrlRef = useRef<string>('');
  const isSearchingRef = useRef<boolean>(false);
  const prevUrlRef = useRef<string>(url);
  const hintTimerRef = useRef<number | null>(null);
  const debouncedTimerRef = useRef<number | null>(null);

  const showNonBlockingHint = (msg: string) => {
    if (hintTimerRef.current) clearTimeout(hintTimerRef.current);
    setHint(msg);
    hintTimerRef.current = window.setTimeout(() => {
      setHint(null);
    }, 5000);
  };

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      if (hintTimerRef.current) clearTimeout(hintTimerRef.current);
      if (debouncedTimerRef.current) clearTimeout(debouncedTimerRef.current);
    };
  }, []);

  // Sync prevUrlRef if prop url changes externally
  useEffect(() => {
    prevUrlRef.current = url;
  }, [url]);

  // Trigger search on detected paste of valid supported URL — executed exactly once
  const triggerAutoSearch = (targetUrl: string) => {
    const trimmed = targetUrl.trim();
    if (!trimmed) return;
    const normalized = normalizeInputUrl(trimmed);
    if (!isValidSupportedUrl(normalized)) return;

    if (loading || isSearchingRef.current || lastSearchedUrlRef.current === normalized) {
      return;
    }

    lastSearchedUrlRef.current = normalized;
    isSearchingRef.current = true;
    setHint(null);
    setLocalError(null);
    onChange(normalized);
    onSubmit(normalized);

    window.setTimeout(() => {
      isSearchingRef.current = false;
    }, 800);
  };

  // Handle manual submit (clicking Search CTA or pressing Enter)
  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (loading) return;
    const trimmed = url.trim();
    if (!trimmed) {
      setLocalError('Please paste or type a video link first.');
      inputRef.current?.focus();
      return;
    }
    const normalized = normalizeInputUrl(trimmed);
    if (normalized !== trimmed) {
      onChange(normalized);
    }
    setLocalError(null);
    setHint(null);
    lastSearchedUrlRef.current = normalized;
    onSubmit(normalized);
  };

  // Clipboard Paste Button handler (reads system clipboard if permitted, device-aware)
  const handlePasteButtonClick = async () => {
    if (loading) return;
    setLocalError(null);
    let pastedText = '';

    if (navigator.clipboard && navigator.clipboard.readText) {
      try {
        pastedText = await navigator.clipboard.readText();
      } catch {
        // Clipboard read permission unavailable or denied on mobile touch browsers
      }
    }

    if (pastedText && pastedText.trim()) {
      setHint(null);
      triggerAutoSearch(pastedText.trim());
    } else {
      inputRef.current?.focus();
      const isMobile =
        typeof window !== 'undefined' &&
        (/Android|iPhone|iPad|iPod/i.test(navigator.userAgent) || window.innerWidth < 768);

      showNonBlockingHint(
        isMobile
          ? 'Tap & hold the box, then tap Paste (or tap clipboard above keyboard)'
          : 'Paste your link here (Ctrl+V / Cmd+V)'
      );
    }
  };

  // Native input paste event (Ctrl+V, Cmd+V, Right-Click > Paste, Mobile long-press Paste)
  const handleNativePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    setHint(null);
    const pastedData = e.clipboardData?.getData('text') || '';
    const trimmed = pastedData.trim();
    if (trimmed && isValidSupportedUrl(trimmed)) {
      const normalized = normalizeInputUrl(trimmed);
      setTimeout(() => {
        onChange(normalized);
        triggerAutoSearch(normalized);
      }, 10);
      return;
    }

    // Microtask fallback for iOS Safari WebKit where clipboardData may be populated asynchronously
    setTimeout(() => {
      const fieldVal = (inputRef.current?.value || '').trim();
      if (fieldVal && isValidSupportedUrl(fieldVal)) {
        const normalized = normalizeInputUrl(fieldVal);
        onChange(normalized);
        triggerAutoSearch(normalized);
      }
    }, 30);
  };

  // Mobile virtual keyboard input (Gboard clipboard chip, iOS QuickType autofill, etc.)
  const handleInput = (e: React.FormEvent<HTMLInputElement>) => {
    const nativeEvent = e.nativeEvent as any;
    const targetVal = (e.target as HTMLInputElement).value;
    if (!targetVal || !targetVal.trim()) return;

    const inputType = nativeEvent?.inputType || '';
    // Support all mobile keyboard paste / autofill types:
    // 'insertFromPaste' (standard paste)
    // 'insertReplacementText' (iOS Safari / autocorrect / autofill)
    // 'insertFromDrop' (drag and drop)
    // 'insertText' (Gboard clipboard chip or multi-char insertion)
    const isMobilePasteLike =
      inputType === 'insertFromPaste' ||
      inputType === 'insertReplacementText' ||
      inputType === 'insertFromDrop' ||
      (inputType === 'insertText' && targetVal.trim().length > 10);

    if (isMobilePasteLike && isValidSupportedUrl(targetVal.trim())) {
      const normalized = normalizeInputUrl(targetVal.trim());
      triggerAutoSearch(normalized);
    }
  };

  // Listen for custom paste and hint events dispatched by Header or other components
  useEffect(() => {
    const handleCustomPasteEvent = (e: Event) => {
      const customEvent = e as CustomEvent<{ text?: string }>;
      const text = customEvent.detail?.text;
      if (text && text.trim()) {
        triggerAutoSearch(text);
      } else {
        handlePasteButtonClick();
      }
    };

    const handleCustomHintEvent = (e: Event) => {
      const customEvent = e as CustomEvent<{ hint?: string }>;
      if (customEvent.detail?.hint) {
        showNonBlockingHint(customEvent.detail.hint);
      }
    };

    window.addEventListener('mediaflow:paste-url', handleCustomPasteEvent);
    window.addEventListener('mediaflow:paste-hint', handleCustomHintEvent);
    return () => {
      window.removeEventListener('mediaflow:paste-url', handleCustomPasteEvent);
      window.removeEventListener('mediaflow:paste-hint', handleCustomHintEvent);
    };
  }, [loading, onChange, onSubmit]);

  const handleClear = () => {
    onChange('');
    setLocalError(null);
    setHint(null);
    lastSearchedUrlRef.current = '';
    prevUrlRef.current = '';
    if (debouncedTimerRef.current) clearTimeout(debouncedTimerRef.current);
    inputRef.current?.focus();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    const prevVal = prevUrlRef.current;
    prevUrlRef.current = val;

    onChange(val);
    if (localError) setLocalError(null);
    if (hint) setHint(null);
    if (val !== lastSearchedUrlRef.current) {
      lastSearchedUrlRef.current = '';
    }

    if (debouncedTimerRef.current) {
      clearTimeout(debouncedTimerRef.current);
    }

    const trimmed = val.trim();
    if (trimmed && isValidSupportedUrl(trimmed)) {
      const normalized = normalizeInputUrl(trimmed);
      const lengthDiff = Math.abs(val.length - prevVal.length);
      // Batch insertion: mobile keyboard clipboard chip, paste, or autocomplete
      const isBatchInsertion = lengthDiff > 2 || (prevVal === '' && val.length > 5);

      if (isBatchInsertion) {
        triggerAutoSearch(normalized);
      } else {
        // Debounced search when user is actively modifying a valid URL
        debouncedTimerRef.current = window.setTimeout(() => {
          triggerAutoSearch(normalized);
        }, 450);
      }
    }
  };


  const displayError = error || localError;

  return (
    <div className="url-input-container">
      <form onSubmit={handleSubmit} className="url-input-form" noValidate>
        {/* Inner Input Card / Pill */}
        <div className="url-input-wrapper">
          <div className="url-input-field-wrapper">
            {/* Link Icon */}
            <span className="url-input-icon" aria-hidden="true">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
              </svg>
            </span>

            <input
              ref={inputRef}
              id="media-url-input"
              type="url"
              className="url-input-field"
              value={url}
              onChange={handleInputChange}
              onPaste={handleNativePaste}
              onInput={handleInput}
              placeholder={placeholder}
              disabled={loading}
              autoComplete="off"
              autoCorrect="off"
              autoCapitalize="off"
              spellCheck="false"
              aria-label="Video URL input"
              aria-invalid={!!displayError}
              aria-describedby={displayError ? 'url-error-msg' : hint ? 'url-paste-hint-msg' : undefined}
            />

            {url ? (
              <button
                type="button"
                className="clear-btn"
                onClick={handleClear}
                aria-label="Clear input URL"
                title="Clear"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            ) : (
              <button
                type="button"
                className="paste-quick-btn"
                onClick={handlePasteButtonClick}
                aria-label="Paste URL from clipboard"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                </svg>
                <span>Paste</span>
              </button>
            )}
          </div>

          <button
            type="submit"
            className="btn-search-cta"
            disabled={loading || !url.trim()}
            aria-busy={loading}
          >
            {loading ? (
              <>
                <svg
                  className="spinner"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                >
                  <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
                  <path d="M12 2a10 10 0 0 1 10 10" />
                </svg>
                <span>Searching...</span>
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
                <span>Search</span>
              </>
            )}
          </button>
        </div>

        {/* Small non-blocking hint (when clipboard permission unavailable/denied) */}
        {hint && (
          <div id="url-paste-hint-msg" className="url-paste-hint" role="status">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="16" x2="12" y2="12" />
              <line x1="12" y1="8" x2="12.01" y2="8" />
            </svg>
            <span>{hint}</span>
          </div>
        )}

        {/* Real Error message (only when user submits empty or invalid URL) */}
        {displayError && (
          <p id="url-error-msg" className="url-error-text" role="alert">
            {displayError}
          </p>
        )}

        {/* FetchMedia Status Line */}
        <div className="url-input-meta">
          <div className="url-meta-left">
            <span className={`meta-status-dot ${loading ? 'amber animate-pulse' : 'green'}`} />
            <span className="meta-status-label">{loading ? 'Analyzing' : 'Ready'}</span>
            <span className="meta-sep">•</span>
            <span className="meta-format-desc">Supports 1080p, 4K &amp; 320kbps MP3</span>
          </div>
          <span className="url-meta-right">Safe SSL Worker</span>
        </div>
      </form>
    </div>
  );
};
