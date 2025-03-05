import { useQuery } from "@tanstack/react-query";
import { UserSubscription } from "~/lib/types";

export const useUser = (fid?: number) => {
  const query = useQuery<UserSubscription[]>({
    queryKey: ["user", fid],
    queryFn: async () => {
      if (!fid) return [];

      const response = await fetch(`/api/user?fid=${fid}`);
      if (!response.ok) throw new Error("Failed to fetch subscriptions");

      return await response.json();
    },
    enabled: !!fid,
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
      refetch: query.refetch,
    },
  };
};
