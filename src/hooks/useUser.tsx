import { useQuery } from "@tanstack/react-query";
import { UserContext, UserSubscription, SubscriptionTier } from "~/lib/types";

const tierConfigs: Record<number, SubscriptionTier> = {
  1: { id: 1, tierName: "Maschine Membe", maxProjects: 1 },
  2: { id: 2, tierName: "Maschine Pro" },
  3: { id: 3, tierName: "Maschine Human Hybrid" }, // undefined means unlimited
};

const HYPERSUB_CONTRACT_ADDRESS = "0x2211e467d0c210F4bdebF4895c25569D93225CFc";

export const useUser = (user?: UserContext) => {
  const query = useQuery<UserSubscription[]>({
    queryKey: ["user", user?.fid],
    queryFn: async () => {
      if (!user?.fid) return [];
      
      const response = await fetch(`/api/user?fid=${user.fid}`);
      if (!response.ok) throw new Error("Failed to fetch subscriptions");
      
      const data = await response.json();
      type SubscriptionData = {
        contract_address: string;
        expires_at: string;
        tier: {
          id: string;
        };
      };

      const maschineSubscriptions = data.subscribed_to.filter(
        (sub: SubscriptionData): boolean =>
          sub.contract_address.toLowerCase() ===
          HYPERSUB_CONTRACT_ADDRESS.toLowerCase(),
      );

      return maschineSubscriptions.map((sub: SubscriptionData) => {
        const tierId = Number(sub.tier.id);
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
    },
    enabled: !!user?.fid,
  });

  const activeSubscription = query.data
    ?.filter((sub) => sub.isActive)
    .sort((a, b) => (b.subscribedTier || 0) - (a.subscribedTier || 0))[0];

  return {
    subscriptions: {
      data: query.data || [],
      active: activeSubscription,
      loading: query.isLoading,
      error: query.error,
      hasActive: !!activeSubscription?.isActive,
      maxProjects: activeSubscription?.maxProjects,
    },
  };
};
