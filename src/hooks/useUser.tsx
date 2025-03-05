import { useEffect, useState } from 'react';
import { UserContext, UserSubscription } from '@/lib/types';

const tierConfigs: Record<number, SubscriptionTier> = {
  1: { id: 1, tierName: 'Starter', maxProjects: 1 },
  2: { id: 2, tierName: 'Pro', maxProjects: 3 },
  3: { id: 3, tierName: 'Unlimited' }, // undefined means unlimited
};

export const useUser = (user?: UserContext) => {
  const [subscriptions, setSubscriptions] = useState<UserSubscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchSubscriptions = async () => {
      try {
        if (!user?.fid) {
          setLoading(false);
          return;
        }

        const contractAddress = process.env.NEXT_PUBLIC_HYPERSUB_CONTRACT_ADDRESS;
        if (!contractAddress) {
          throw new Error('HYPERSUB_CONTRACT_ADDRESS not configured');
        }

        const response = await fetch(
          `https://api.neynar.com/v2/farcaster/user/subscribed_to?fid=${user.fid}&subscription_provider=fabric_stp`,
          {
            headers: {
              'x-api-key': process.env.NEXT_PUBLIC_NEYNAR_API_KEY!,
            },
          }
        );

        if (!response.ok) throw new Error('Failed to fetch subscriptions');
        
        const data = await response.json();
        const ourSubs = data.subscribed_to.filter((sub: any) => 
          sub.contract_address.toLowerCase() === contractAddress.toLowerCase()
        );

        const mapped = ourSubs.map((sub: any) => {
          const tierId = sub.tier.id;
          const tier = tierConfigs[tierId] || { tierName: 'Unknown' };
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
        setError(err instanceof Error ? err : new Error('Subscription check failed'));
      } finally {
        setLoading(false);
      }
    };

    fetchSubscriptions();
  }, [user?.fid]);

  const activeSubscription = subscriptions
    .filter(sub => sub.isActive)
    .sort((a, b) => (b.subscribedTier || 0) - (a.subscribedTier || 0))[0];

  return {
    subscriptions: {
      data: subscriptions,
      active: activeSubscription,
      loading,
      error,
      hasActive: !!activeSubscription?.isActive,
      maxProjects: activeSubscription?.maxProjects,
    },
    // Can add other user-related data here
  };
};
