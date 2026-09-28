import React from 'react';

export interface PlatformThemeProviderProps {
  platform: 'youtube' | 'instagram' | 'x' | 'facebook' | 'pinterest' | 'reddit' | 'generic' | 'all' | string;
  children: React.ReactNode;
}

export const PlatformThemeProvider: React.FC<PlatformThemeProviderProps> = ({ platform, children }) => {
  return (
    <div data-platform={platform}>
      {children}
    </div>
  );
};
