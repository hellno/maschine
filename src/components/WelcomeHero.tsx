"use client";

import Link from "next/link";
import FancyLargeButton from "./FancyLargeButton";
import { useFrameSDK } from "~/hooks/useFrameSDK";
import { useUser } from "~/hooks/useUser";
import {
  fetchContext,
  prepareMint,
  tierDetail,
} from "@withfabric/protocol-sdks/stpv2";
import { useAccount } from "wagmi";
import { useCallback, useState } from "react";
import { LoaderCircle } from "lucide-react";
import { useProjects } from "~/hooks/useProjects";
import { formatEther } from "viem";
import { useBalance } from "wagmi";
import { base } from "wagmi/chains";
import Swap from "./Swap";
import {
  DEFAULT_SUBSCRIPTION_TIER,
  getMinSubscriptionAmount,
  HYPERSUB_CONTRACT_ADDRESS,
  MASCHINE_PRO_SUBSCRIPTION_TIER,
} from "~/lib/hypersub";

function bigIntReplacer(key: string, value: unknown) {
  if (typeof value === "bigint") {
    return value.toString() + "n";
  }
  return value;
}

const WelcomeHero = () => {
  const [isMinting, setIsMinting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const { address } = useAccount();
  const { context } = useFrameSDK();
  const {
    subscriptions: {
      hasActive: hasActiveSubscription,
      active,
      maxProjects,
      loading,
      refetch,
    },
  } = useUser(context?.user?.fid);
  const { projects } = useProjects(context?.user?.fid);
  const { data: balance } = useBalance({
    address,
    chainId: base.id,
  });

  const canCreateMoreProjects = !maxProjects || projects.length < maxProjects;

  const onMintSubscription = useCallback(
    async (tierId?: number | undefined) => {
      if (!address) return;
      setError(null);
      setIsMinting(true);

      const hypersubContext = await fetchContext({
        contractAddress: HYPERSUB_CONTRACT_ADDRESS,
        account: address,
      });

      const subscriptionAmount = getMinSubscriptionAmount(tierId);
      if (hypersubContext.holdings.balance < subscriptionAmount) {
        setMessage(`Need ${formatEther(subscriptionAmount)} ETH`);
        setIsMinting(false);
        return;
      }

      const tier = await tierDetail({
        contractAddress: HYPERSUB_CONTRACT_ADDRESS,
        tierId: tierId || DEFAULT_SUBSCRIPTION_TIER,
      });

      setMessage(
        `Minting subscription... ${JSON.stringify(tier, bigIntReplacer)}`,
      );
      try {
        const mint = await prepareMint({
          contractAddress: HYPERSUB_CONTRACT_ADDRESS,
          amount: subscriptionAmount,
        });
        setMessage(
          `Got mint for tier ${JSON.stringify(tier, bigIntReplacer)} ${JSON.stringify(mint, bigIntReplacer)}`,
        );
        const receipt = await mint();
        console.log("receipt", receipt);
      } catch (error) {
        console.error(error);
        setError(
          `Failed to mint subscription ${tier}: ${JSON.stringify(error, bigIntReplacer)}`,
        );
      }

      await refetch();
      setIsMinting(false);
    },
    [address, refetch],
  );

  const renderSubscribeButton = (
    tierId: number,
    disabled: boolean | undefined = false,
  ) => {
    if (isMinting) {
      return (
        <div className="h-16 align-center text-center w-full flex flex-row justify-center">
          <LoaderCircle className="w-6 h-6 animate-spin" />
          <p className="ml-2 font-medium text-xl">Minting...</p>
        </div>
      );
    }

    return (
      <div className="flex flex-col gap-2">
        <button
          onClick={() => onMintSubscription(tierId)}
          disabled={isMinting || disabled}
          className="relative inline-flex h-12 overflow-hidden rounded-full p-[1px] focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 focus:ring-offset-slate-50 disabled:opacity-100 disabled:cursor-not-allowed transition-opacity"
        >
          <span className="absolute inset-[-500%] bg-gray-100 dark:bg-gray-800 border" />
          <span className="inline-flex h-full w-full items-center justify-center rounded-full bg-slate-950 px-6 py-2 text-xl font-medium text-white backdrop-blur-3xl hover:bg-slate-900 disabled:bg-gray-300 disabled:text-gray-500">
            Upgrade Subscription
          </span>
        </button>
        {disabled && (
          <p className="text-sm text-red-500 dark:text-red-400">
            Insufficient ETH balance to upgrade
          </p>
        )}
      </div>
    );
  };

  const hasEnoughBalanceToUpgradeToTier = (tierId: number) => {
    const minAmount = getMinSubscriptionAmount(tierId);
    return balance && balance.value >= minAmount;
  };

  const renderSwapForTier = (tierId: number) => {
    const minAmount = getMinSubscriptionAmount(tierId);

    return (
      <div className="flex flex-col align-center text-center justify-center gap-4">
        <p className="text-pretty font-medium text-gray-600 ">
          {balance
            ? `Swap below to get ${Number(formatEther(minAmount - balance.value)).toFixed(4)} more ETH to upgrade.`
            : "Swap below to get more ETH to upgrade"}
        </p>
        <div className="flex h-full">
          <Swap />
        </div>
      </div>
    );
  };

  const renderSubscribeFlow = () => {
    if (loading) {
      return null;
    }

    if (hasActiveSubscription) {
      const hasBalanceToUpgrade = hasEnoughBalanceToUpgradeToTier(
        MASCHINE_PRO_SUBSCRIPTION_TIER,
      );
      return (
        <div className="flex flex-col p-2 pt-0 space-y-4">
          {active?.subscribedTier === DEFAULT_SUBSCRIPTION_TIER && (
            <div className="flex flex-col gap-4">
              {renderSubscribeButton(
                MASCHINE_PRO_SUBSCRIPTION_TIER,
                !hasBalanceToUpgrade,
              )}
              {!hasBalanceToUpgrade &&
                renderSwapForTier(MASCHINE_PRO_SUBSCRIPTION_TIER)}
            </div>
          )}
          <div className="flex flex-col">
            <p>Thank your for subscribing.</p>
            <p className="">
              {projects.length} / {maxProjects || "infinite"} frames used.
            </p>
          </div>
        </div>
      );
    } else {
      const hasBalanceToUpgrade = hasEnoughBalanceToUpgradeToTier(
        MASCHINE_PRO_SUBSCRIPTION_TIER,
      );
      return (
        <div className="p-2 mt-4 justify-center gap-4">
          {renderSubscribeButton(
            DEFAULT_SUBSCRIPTION_TIER,
            !hasBalanceToUpgrade,
          )}
          {!hasBalanceToUpgrade &&
            renderSwapForTier(MASCHINE_PRO_SUBSCRIPTION_TIER)}
        </div>
      );
    }
  };
  return (
    <div className="mx-auto max-w-xs lg:max-w-3xl lg:pt-8">
      {/* <div className="mt-8 flex justify-center">
        <img
          alt="Frameception Logo"
          src="/icon.png"
          className="h-20 w-20 rounded-xl"
        />
      </div> */}
      <h1 className="mx-auto max-w-sm mt-4 text-pretty font-bold tracking-tight text-gray-900 text-5xl md:text-6xl dark:text-gray-100 lg:max-w-xl">
        Turn your idea
        <br className="hidden md:inline" /> into a{" "}
        <p className="bg-gradient-to-br from-purple-400 via-purple-600-600 to-blue-700 bg-clip-text text-transparent hover:to-blue-700/80 hover:from-purple-500">
          Farcaster frame in minutes
        </p>
      </h1>
      <p className="mt-6 mx-4 text-pretty tracking-tight text-lg font-medium text-gray-600 sm:text-xl/8 dark:text-gray-300 max-w-2xl">
        Create your own share-able frame in a Farcaster frame, right here.
      </p>
      <div className="flex flex-col text-md text-pretty text-gray-600 sm:text-xl/8 dark:text-gray-400 max-w-2xl">
        {canCreateMoreProjects ? (
          <Link className="pt-8 pb-2 flex justify-center" href="/projects/new">
            <FancyLargeButton text="Start Building" />
          </Link>
        ) : (
          <div className="mt-6 flex flex-col gap-4">
            {renderSubscribeFlow()}
            <a
              href="https://hypersub.xyz/s/maschine?referrer=0x6d9ffaede2c6cd9bb48bece230ad589e0e0d981c"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-700 underline hover:text-blue-500"
            >
              Visit Hypersub for details
            </a>
          </div>
        )}
        {context?.user?.fid.toString() === "13596" && (
          <div className="mt-4 mx-auto max-w-xs flex flex-col items-center">
            <p>message: {message}</p>
            <p>address: {address}</p>
            <p>context: {JSON.stringify(context)}</p>
            {error && (
              <p className="mt-4 mx-auto max-w-xs bg-red-800 text-white">
                {error}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default WelcomeHero;
