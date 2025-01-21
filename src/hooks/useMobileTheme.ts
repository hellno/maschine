'use client';

import { useEffect } from 'react';
import { useTheme } from 'next-themes';

export function useMobileTheme() {
  const { setTheme } = useTheme();

  useEffect(() => {
    const isMobile = /Mobi|Android/i.test(navigator.userAgent);
    if (isMobile) {
      setTheme('dark');
      localStorage.setItem('theme', 'dark');
    }
  }, [setTheme]);
}
