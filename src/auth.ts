import { AuthOptions, getServerSession } from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials";
import { createAppClient, viemConnector } from "@farcaster/auth-client";

declare module "next-auth" {
  interface Session {
    user: {
      fid?: number;
      email?: string;
      walletAddress?: string;
      authMethod: 'farcaster' | 'email' | 'web3' | 'anonymous';
    };
  }
}

export const authOptions: AuthOptions = {
    // Configure one or more authentication providers
  providers: [
    CredentialsProvider({
      name: "Sign in with Farcaster",
      credentials: {
        message: {
          label: "Message",
          type: "text",
          placeholder: "0x0",
        },
        signature: {
          label: "Signature",
          type: "text",
          placeholder: "0x0",
        },
        // In a production app with a server, these should be fetched from
        // your Farcaster data indexer rather than have them accepted as part
        // of credentials.
        name: {
          label: "Name",
          type: "text",
          placeholder: "0x0",
        },
        pfp: {
          label: "Pfp",
          type: "text",
          placeholder: "0x0",
        },
      },
      async authorize(credentials, req) {
        const csrfToken = req?.body?.csrfToken;
        const appClient = createAppClient({
          ethereum: viemConnector(),
        });

        const verifyResponse = await appClient.verifySignInMessage({
          message: credentials?.message as string,
          signature: credentials?.signature as `0x${string}`,
          domain: new URL(process.env.NEXTAUTH_URL ?? '').hostname,
          nonce: csrfToken,
        });
        const { success, fid } = verifyResponse;

        if (!success) {
          return null;
        }

        return {
          id: fid.toString(),
          authMethod: 'farcaster',
          fid: fid,
        };
      },
    }),
  ],
  callbacks: {
    session: async ({ session, token, user }) => {
      if (session.user) {
        session.user = {
          ...session.user,
          ...user, // Contains authMethod and other fields
          fid: token.sub ? parseInt(token.sub) : undefined
        };
      }
      return session;
    },
  }
}

export const getSession = () => getServerSession(authOptions)
