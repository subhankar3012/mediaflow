import React from 'react';

export interface ErrorAlertProps {
  message: string;
  onDismiss?: () => void;
  onRetry?: () => void;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({ message, onDismiss, onRetry }) => {
  if (!message) return null;

  return (
    <div
      className="editorial-error-alert"
      role="alert"
      aria-live="assertive"
    >
      <div className="error-alert-content">
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ flexShrink: 0, marginTop: '2px' }}
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        <div style={{ flex: 1 }}>
          <p className="error-message-text">{message}</p>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="error-retry-btn"
            >
              Try again
            </button>
          )}
        </div>
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="error-dismiss-btn"
          aria-label="Dismiss error"
        >
          ✕
        </button>
      )}
    </div>
  );
};
