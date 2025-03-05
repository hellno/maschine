import { useEffect, useState } from "react";
import { UserContext, UserSubscription, SubscriptionTier } from "~/lib/types";

const tierConfigs: Record<number, SubscriptionTier> = {
  1: { id: 1, tierName: "Maschine Membe", maxProjects: 1 },
  2: { id: 2, tierName: "Maschine Pro" },
  3: { id: 3, tierName: "Maschine Human Hybrid" }, // undefined means unlimited
};

const HYPERSUB_CONTRACT_ADDRESS = "0x2211e467d0c210F4bdebF4895c25569D93225CFc";

// ai! update to use tanstack query like in `useProjects.ts`
export const useUser = (user?: UserContext) => {
  const [subscriptions, setSubscriptions] = useState<UserSubscription[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchSubscriptions = async () => {
      try {
        if (!user?.fid) {
          setIsLoading(false);
          return;
        }

        const response = await fetch(`/api/user?fid=${user.fid}`);

        if (!response.ok) throw new Error("Failed to fetch subscriptions");

        const data = await response.json();
        type NewType = {
          contract_address: string;
          expires_at: string;
          tier: {
            id: string;
          };
        };

        console.log("data", data);
        const maschineSubscriptions = data.subscribed_to.filter(
          (sub: NewType): boolean =>
            sub.contract_address.toLowerCase() ===
            HYPERSUB_CONTRACT_ADDRESS.toLowerCase(),
        );

        const mapped = maschineSubscriptions.map((sub: NewType) => {
          const tierId = sub.tier.id;
          const tier = tierConfigs[tierId] || { tierName: "Unknown" };
          const expiresAt = new Date(sub.expires_at);

          return {
            subscribedTier: tierId,
            tierName: tier.tierName,
            maxProjects: tier.maxProjects,
            isActive: expiresAt > new Date(),
            expires_at: sub.expires_at,
          };
        });

        setSubscriptions(mapped);
      } catch (err) {
        setError(
          err instanceof Error ? err : new Error("Subscription check failed"),
        );
      } finally {
        setIsLoading(false);
      }
    };

    fetchSubscriptions();
  }, [user?.fid]);

  const activeSubscription = subscriptions
    .filter((sub) => sub.isActive)
    .sort((a, b) => (b.subscribedTier || 0) - (a.subscribedTier || 0))[0];

  return {
    subscriptions: {
      data: subscriptions,
      active: activeSubscription,
      loading: isLoading,
      error,
      hasActive: !!activeSubscription?.isActive,
      maxProjects: activeSubscription?.maxProjects,
    },
    // Can add other user-related data here
  };
};
