"use client";

import { ThemeProvider } from "~/components/theme-provider";
import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import type { Session } from "next-auth";
import { SessionProvider } from "next-auth/react";
import posthog from "posthog-js";
import { PostHogProvider } from "posthog-js/react";

if (typeof window !== "undefined" && process.env.NEXT_PUBLIC_POSTHOG_KEY) {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
    persistence: 'memory', // Avoid cookies/localStorage
    person_profiles: 'identified_only',
    loaded: (posthog) => {
      // Generate anonymous ID server-side when needed
      if (posthog.get_distinct_id() === null) {
        posthog.register({
          distinct_id: crypto.randomUUID() // Generate temp browser-session-only ID
        })
      }
    }
  });
}

const WagmiProvider = dynamic(
  () => import("~/components/providers/WagmiProvider"),
  { ssr: false }
);

export function CSPostHogProvider({ children }: { children: React.ReactNode }) {
  return <PostHogProvider client={posthog}>{children}</PostHogProvider>;
}

export function Providers({
  session,
  children,
}: {
  session: Session | null;
  children: React.ReactNode;
}) {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    setIsMobile(/Mobi|Android/i.test(navigator.userAgent));
  }, []);

  return (
    <ThemeProvider
      attribute="class"
      defaultTheme={isMobile ? "dark" : "system"}
      forcedTheme={isMobile ? "dark" : undefined}
      enableSystem={!isMobile}
      disableTransitionOnChange
    >
      <CSPostHogProvider>
        <SessionProvider session={session}>
          <WagmiProvider>{children}</WagmiProvider>
        </SessionProvider>
      </CSPostHogProvider>
    </ThemeProvider>
  );
}
