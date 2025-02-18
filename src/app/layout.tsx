import "~/app/globals.css";

import type { Metadata } from "next";
import { getSession } from "~/auth";
import { Providers } from "~/app/providers";
import Script from "next/script";
import Layout from "~/components/Layout";

export const metadata: Metadata = {
  title: "frameception",
  description: "Farcaster frame to build Farcaster frames",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const session = await getSession();

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <Script id="touch-init" strategy="beforeInteractive">
          {`
            (function() {
              // Add touch detection class only
              document.documentElement.classList.add(
                'ontouchstart' in window || navigator.maxTouchPoints > 0
                  ? 'touch'
                  : 'no-touch'
              );
            })();
          `}
        </Script>
      </head>
      <body className="min-h-screen bg-background antialiased">
        <Providers session={session}>
          <Layout>{children}</Layout>
        </Providers>
      </body>
    </html>
  );
}
