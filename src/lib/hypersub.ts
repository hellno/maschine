import { SubscriptionTier } from "./types";

export const HYPERSUB_CONTRACT_ADDRESS =
  "0x2211e467d0c210F4bdebF4895c25569D93225CFc";

export const DEFAULT_SUBSCRIPTION_TIER = 3; // maschine member
export const MASCHINE_PRO_SUBSCRIPTION_TIER = 1; // maschine pro member

export const TIERS: Record<number, SubscriptionTier> = {
  1: { id: 1, tierName: "Maschine Pro", priceInEth: 5000000000000000n }, // undefined means unlimited
  2: {
    id: 2,
    tierName: "Maschine Human Hybrid",
    priceInEth: 1000000000000000000n,
  },
  3: {
    id: 3,
    tierName: "Maschine Member",
    maxProjects: 2,
    priceInEth: 690000000000000n,
    priceToBecomeMember: 690000000000000n,
  },
};

export const getMinSubscriptionAmount = (
  tierId: number | undefined = DEFAULT_SUBSCRIPTION_TIER,
): bigint => {
  const baseAmount = TIERS[tierId].priceInEth;
  const priceToBecomeMember = TIERS[tierId].priceToBecomeMember || 0n;
  return baseAmount + priceToBecomeMember;
};
