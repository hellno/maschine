"use client";

import { ThemeProvider } from "~/components/theme-provider";
import { useEffect, useState } from "react";
import type { Session } from "next-auth";
import { SessionProvider } from "next-auth/react";
import posthog from "posthog-js";
import { PostHogProvider } from "posthog-js/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { WagmiProvider } from "wagmi";
import { config } from "~/app/wagmi";

if (typeof window !== "undefined" && process.env.NEXT_PUBLIC_POSTHOG_KEY) {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
    persistence: "memory",
    person_profiles: "identified_only",
    loaded: (ph) => {
      // Generate anonymous session ID without identifying
      const sessionId = ph.get_distinct_id() || crypto.randomUUID();
      ph.register({ session_id: sessionId });

      // Temporary distinct ID that will be aliased later
      if (!ph.get_distinct_id()) {
        ph.reset(true); // Ensure clean state
      }
    },
  });
}

const queryClient = new QueryClient();

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
          <WagmiProvider config={config}>
            <QueryClientProvider client={queryClient}>
              {children}
            </QueryClientProvider>
          </WagmiProvider>
        </SessionProvider>
      </CSPostHogProvider>
    </ThemeProvider>
  );
}
