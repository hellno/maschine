"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, CardContent } from "~/components/ui/card";
import { useAccount } from "wagmi";
import { CheckIcon, Loader2 } from "lucide-react";
import { BigPurpleButton } from "~/components/ui/BigPurpleButton";
import FancyLargeButton from "./FancyLargeButton";
import { FrameContext } from "@farcaster/frame-sdk";
import Link from "next/link";

type AccessCheckProps = {
  userContext?: FrameContext["user"];
  onAccessGranted: () => void;
};

type Requirement = {
  idx: number;
  isValid: boolean;
  name: string;
  message?: string;
};

export const AccessCheck = ({
  userContext,
  onAccessGranted,
}: AccessCheckProps) => {
  const { address } = useAccount();
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [isCheckingAccess, setIsCheckingAccess] = useState(true);
  const [hasAccess, setHasAccess] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const checkAccess = useCallback(async () => {
    try {
      if (!userContext?.fid) {
        const mockRequirements: Requirement[] = [
          {
            idx: 0,
            isValid: false,
            name: "Farcaster Account",
            message: "No Farcaster account detected",
          },
        ];
        setRequirements(mockRequirements);
        setIsCheckingAccess(false);

        return;
      }

      const response = await fetch("/api/check-access", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ fids: [userContext.fid], address }),
      });

      if (!response.ok) {
        throw new Error("Access check failed");
      }

      const data = await response.json();
      setRequirements(data.requirements || []);
      setHasAccess(data.hasAccess);
      setActionMessage(data.actionMessage);
      setIsCheckingAccess(false);
    } catch (error) {
      console.error("Access check failed:", error);
      const mockRequirements: Requirement[] = [
        {
          idx: 0,
          isValid: false,
          name: "Farcaster Account",
          message: "Error validating account status",
        },
      ];
      setRequirements(mockRequirements);
      setIsCheckingAccess(false);
      setActionMessage("register_farcaster_account");
    }
  }, [address, userContext]);

  useEffect(() => {
    checkAccess();
  }, [checkAccess]);

  if (isCheckingAccess) {
    return (
      <div className="flex items-center justify-center p-8 gap-x-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        Checking access...
      </div>
    );
  }

  const renderButton = () => {
    if (hasAccess) {
      return (
        <FancyLargeButton text="Start Building" onClick={onAccessGranted} />
      );
    }
    if (!actionMessage || actionMessage === "register_farcaster_account") {
      return (
        <Link href="https://warpcast.com">
          <BigPurpleButton>Create Farcaster account</BigPurpleButton>
        </Link>
      );
    }

    // if (actionMessage === "mint_nft") {
    //   return (
    //     <Link href="/mint-nft">
    //       <BigPurpleButton>Mint NFT</BigPurpleButton>
    //     </Link>
    //   );
    // }
  };

  return (
    <div className="flex flex-col items-center justify-center gap-4 p-8">
      <Card className="w-full max-w-md">
        <CardContent>
          <h3 className="text-xl font-semibold m-4">
            {hasAccess ? "You have access!" : "You don't have access, yet"}
          </h3>
          <div className="mt-4 flex justify-center">{renderButton()}</div>
          <div className="mt-8 space-y-4">
            {requirements.map((req) => (
              <div key={req.idx} className="flex flex-col space-y-1">
                <div className="flex items-center gap-2">
                  <span
                    className={`w-5 h-5 rounded-full flex items-center justify-center ${
                      req.isValid
                        ? "bg-green-500 text-white"
                        : "bg-red-500 text-white"
                    }`}
                  >
                    {req.isValid ? <CheckIcon className="h-4 w-4" /> : "✗"}
                  </span>
                  <span className="font-medium">{req.name}</span>
                </div>
                {req.message && (
                  <p className="text-sm text-gray-600 ml-8">{req.message}</p>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
