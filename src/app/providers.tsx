"use client";

import dynamic from "next/dynamic";
import type { Session } from "next-auth"
import { SessionProvider } from "next-auth/react"

//AI! 
// add posthog provider 
// Initialize
// With App router
// If your Next.js app to uses the app router, you can integrate PostHog by creating a providers file in your app folder. This is because the posthog-js library needs to be initialized on the client-side using the Next.js 'use client' directive.

// // app/providers.js
// 'use client'
// import posthog from 'posthog-js'
// import { PostHogProvider } from 'posthog-js/react'

// if (typeof window !== 'undefined') {
//   posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY, {
//     api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
//     person_profiles: 'identified_only', // or 'always' to create profiles for anonymous users as well
//   })
// }
// export function CSPostHogProvider({ children }) {
//     return <PostHogProvider client={posthog}>{children}</PostHogProvider>
// }
// Afterwards, import the PHProvider component in your app/layout.js file and wrap your app with it.

// // app/layout.js
// import './globals.css'
// import { CSPostHogProvider } from './providers'

// export default function RootLayout({ children }) {
//   return (
//     <html lang="en">
//       <CSPostHogProvider>
//         <body>{children}</body>
//       </CSPostHogProvider>
//     </html>
//   )
// }
const WagmiProvider = dynamic(
  () => import("~/components/providers/WagmiProvider"),
  {
    ssr: false,
  }
);

export function Providers({ session, children }: { session: Session | null, children: React.ReactNode }) {
  return (
    <SessionProvider session={session}>
      <WagmiProvider>
        {children}
      </WagmiProvider>
    </SessionProvider>
  );
}
