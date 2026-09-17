import React from 'react';

export interface PlatformThemeProviderProps {
  platform: 'youtube' | 'instagram' | 'generic' | 'all';
  children: React.ReactNode;
}

export const PlatformThemeProvider: React.FC<PlatformThemeProviderProps> = ({ platform, children }) => {
  return (
    <div data-platform={platform}>
      {children}
    </div>
  );
};
