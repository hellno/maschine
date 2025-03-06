"use client";

import Link from "next/link";
import FancyLargeButton from "./FancyLargeButton";
import { useFrameSDK } from "~/hooks/useFrameSDK";
import { useUser } from "~/hooks/useUser";
import { prepareMint, tierDetail } from "@withfabric/protocol-sdks/stpv2";
import { useAccount } from "wagmi";
import { useCallback, useState } from "react";
import { LoaderCircle } from "lucide-react";
import { useProjects } from "~/hooks/useProjects";

const HYPERSUB_CONTRACT_ADDRESS = "0x2211e467d0c210f4bdebf4895c25569d93225cfc";
const DEFAULT_SUBSCRIPTION_TIER = 3; // maschine member
const MASCHINE_PRO_SUBSCRIPTION_TIER = 1; // maschine pro member
const DEFAULT_SUBSCRIPTION_PERIOD = 3n; // 2 months + upfront cost to subscribe

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
  const canCreateMoreProjects = maxProjects
    ? projects.length < maxProjects
    : true;

  const onMintSubscription = useCallback(
    async (tierId?: number | undefined) => {
      if (!address) return;
      setError(null);
      setIsMinting(true);

      const tier = await tierDetail({
        contractAddress: HYPERSUB_CONTRACT_ADDRESS,
        tierId: tierId || DEFAULT_SUBSCRIPTION_TIER,
      });
      setMessage(`Minting subscription... ${JSON.stringify(tier)}`);
      const amount = DEFAULT_SUBSCRIPTION_PERIOD * tier.params.pricePerPeriod;
      try {
        const mint = await prepareMint({
          contractAddress: HYPERSUB_CONTRACT_ADDRESS,
          amount,
        });
        setMessage(
          `Got mint for tier ${JSON.stringify(tier)} ${JSON.stringify(mint)}`,
        );
        const receipt = await mint();
        console.log("receipt", receipt);
      } catch (error) {
        console.error(error);
        setError(
          `Failed to mint subscription ${tier}: ${JSON.stringify(error)}`,
        );
      }

      await refetch();
      setIsMinting(false);
    },
    [address, refetch],
  );

  const renderSubscribeButton = (tierId: number) =>
    isMinting ? (
      <div className="h-16 align-center text-center w-full flex flex-row justify-center">
        <LoaderCircle className="w-6 h-6 animate-spin" />
        <p className="ml-2 font-medium text-xl">Minting...</p>
      </div>
    ) : (
      <button
        onClick={() => onMintSubscription(tierId)}
        disabled={isMinting}
        className="relative inline-flex h-12 overflow-hidden rounded-full p-[1px] focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 focus:ring-offset-slate-50 disabled:opacity-75 disabled:cursor-not-allowed transition-opacity"
      >
        <span className="absolute inset-[-500%] bg-gray-100 border" />
        <span className="inline-flex h-full w-full items-center justify-center rounded-full bg-slate-950 px-6 py-2 text-xl font-medium text-white backdrop-blur-3xl hover:bg-slate-900">
          Upgrade to Maschine Member
        </span>
      </button>
    );

  const renderSubscription = () => {
    if (loading) {
      return null;
    }
    if (hasActiveSubscription) {
      return (
        <div className="p-2 pt-0 space-y-4">
          <p>
            Thank your for subscribing {active?.tierName}
            <br />
            You can create{" "}
            {maxProjects
              ? `${maxProjects} frames`
              : "as many frames as you want"}
            .
          </p>
          {active?.subscribedTier === DEFAULT_SUBSCRIPTION_TIER &&
            renderSubscribeButton(MASCHINE_PRO_SUBSCRIPTION_TIER)}
        </div>
      );
    } else {
      return (
        <div className="p-2 mt-4 justify-center">
          {renderSubscribeButton(DEFAULT_SUBSCRIPTION_TIER)}
        </div>
      );
    }
  };
  return (
    <div className="mx-auto max-w-xs lg:max-w-3xl lg:pt-8">
      <div className="mt-8 flex justify-center">
        <img
          alt="Frameception Logo"
          src="/icon.png"
          className="h-20 w-20 rounded-xl"
        />
      </div>
      <h1 className="mx-auto max-w-xs mt-4 text-pretty text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl md:text-6xl dark:text-gray-100 lg:max-w-xl">
        Turn your idea into a <br className="hidden md:inline" />
        <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          shareable frame in minutes
        </span>
      </h1>
      <p className="mt-6 mx-8 text-pretty text-lg font-medium text-gray-600 sm:text-xl/8 dark:text-gray-400 max-w-2xl">
        Create your own Farcaster frame in a Farcaster frame, right here.
      </p>
      <Link className="pt-8 pb-2 flex justify-center" href="/projects/new">
        <FancyLargeButton text="Start Building" />
      </Link>
      {context?.user?.fid.toString() === "13596" && (
        <div>
          {canCreateMoreProjects ? (
            <Link
              className="pt-8 pb-2 flex justify-center"
              href="/projects/new"
            >
              <FancyLargeButton text="Start Building" />
            </Link>
          ) : (
            <p className="pt-8 pb-2 flex justify-center">
              You have reached your frame limit, upgrade below to create more
              frames.
            </p>
          )}
          {renderSubscription()}
          <p className="mt-4 mx-auto max-w-xs">
            Visit{" "}
            <a
              href="https://hypersub.xyz/s/maschine?referrer=0x6d9ffaede2c6cd9bb48bece230ad589e0e0d981c"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-700 underline hover:text-blue-500"
            >
              Hypersub for details
            </a>
            .
          </p>
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
        </div>
      )}
    </div>
  );
};

export default WelcomeHero;
