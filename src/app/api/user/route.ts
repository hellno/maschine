import { NextResponse } from "next/server";
import { NextRequest } from "next/server";
import { HYPERSUB_CONTRACT_ADDRESS, TIERS } from "~/lib/hypersub";
import {
  NeynarSubscriptionData,
  SubscriptionTier,
  UserSubscription,
} from "~/lib/types";

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const fid = searchParams.get("fid");

    if (!fid) {
      return NextResponse.json(
        { error: "Missing fid parameter" },
        { status: 400 },
      );
    }

    if (!process.env.NEYNAR_API_KEY) {
      return NextResponse.json(
        { error: "Neynar API key not configured" },
        { status: 500 },
      );
    }

    const response = await fetch(
      `https://api.neynar.com/v2/farcaster/user/subscribed_to?fid=${fid}&subscription_provider=fabric_stp`,
      {
        headers: {
          "Content-Type": "application/json",
          api_key: process.env.NEYNAR_API_KEY,
        },
      },
    );

    if (!response.ok) {
      if (response.status === 404) {
        console.log("response", await response.text());
        console.log("response.status", response.status);
        return NextResponse.json([]);
      }
      return NextResponse.json(
        { error: "Failed to fetch subscription status" },
        { status: response.status },
      );
    }

    const data = await response.json();

    const maschineSubscriptions = data.subscribed_to.filter(
      (sub: NeynarSubscriptionData): boolean =>
        sub.contract_address.toLowerCase() ===
        HYPERSUB_CONTRACT_ADDRESS.toLowerCase(),
    );

    const subscriptions = maschineSubscriptions.map(
      (sub: NeynarSubscriptionData) => {
        const tierId = Number(sub.tier.id);
        const tier: SubscriptionTier | undefined = TIERS[tierId];
        const expiresAt = new Date(sub.expires_at);

        if (!tier) {
          throw new Error(`Subscription tier not found for ID: ${tierId}`);
        }

        return {
          subscribedTier: tierId,
          tierName: tier.tierName,
          maxProjects: tier.maxProjects,
          isActive: expiresAt > new Date(),
          expires_at: sub.expires_at,
        } as UserSubscription;
      },
    );
    return NextResponse.json(subscriptions);
  } catch (error) {
    console.error("Error checking subscription:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
