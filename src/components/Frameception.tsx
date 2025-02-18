"use client";

import { useCallback, useState, useMemo, useEffect } from "react";
import { useMobileTheme } from "~/hooks/useMobileTheme";
import { useFrameSDK } from "~/hooks/useFrameSDK";
import { useProjects } from "~/hooks/useProjects";
import { AccessCheck } from "./AccessCheck";
import { ProjectOverviewCard } from "./ProjectOverviewCard";
import { ProjectDetailView } from "./ProjectDetailView";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "~/components/ui/tabs";
import { Card, CardContent } from "~/components/ui/card";
import sdk, { FrameNotificationDetails } from "@farcaster/frame-sdk";
import {
  useAccount,
  useSendTransaction,
  useSignMessage,
  useSignTypedData,
  useWaitForTransactionReceipt,
  useDisconnect,
  useConnect,
  useChainId,
} from "wagmi";
import { BaseError, UserRejectedRequestError } from "viem";

import { config } from "~/components/providers/WagmiProvider";
import { BigPurpleButton } from "~/components/ui/BigPurpleButton";
import { truncateAddress } from "~/lib/truncateAddress";
import { base } from "wagmi/chains";
import { Button } from "./ui/button";
import { ArrowUp, AlertCircle, PlayCircle, Loader2 } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "~/components/ui/sheet";
import { FrameContext, Project } from "~/lib/types";
import WelcomeHero from "./WelcomeHero";

type FlowState =
  | "checkingAccess"
  | "waitForFrameToBePinned"
  | "enteringPrompt"
  | "pending"
  | "success";

export default function Frameception() {
  useMobileTheme();
  const { context, isFramePinned, notificationDetails, lastEvent } =
    useFrameSDK();
  const { projects, isLoading: isLoadingProjects } = useProjects(
    context?.user?.fid
  );

  useEffect(() => {
    if (isFramePinned) {
      setFlowState("enteringPrompt");
    }
  }, [isFramePinned]);

  return (
    <div
      style={{
        paddingTop: context?.client.safeAreaInsets?.top ?? 0,
        paddingBottom: context?.client.safeAreaInsets?.bottom ?? 0,
        paddingLeft: context?.client.safeAreaInsets?.left ?? 0,
        paddingRight: context?.client.safeAreaInsets?.right ?? 0,
      }}
    >
      <div className="mx-auto py-2 px-2 md:px-4 max-w-3xl text-center">
        <WelcomeHero />
        <AccessCheck
          userContext={context?.user}
          onAccessGranted={() => {
            console.log("onAccessGranted");
            // setFlowState("waitForFrameToBePinned");
          }}
        />
        {process.env.NEXT_PUBLIC_URL?.endsWith("cloudflare.com") && (
          <DebugView />
        )}
      </div>
    </div>
  );
}

/**
 * SignMessage Component
 */
function SignMessage() {
  const { isConnected } = useAccount();
  const { connectAsync } = useConnect();
  const {
    signMessage,
    data: signature,
    error: signError,
    isError: isSignError,
    isPending: isSignPending,
  } = useSignMessage();

  const handleSignMessage = useCallback(async () => {
    if (!isConnected) {
      await connectAsync({
        chainId: base.id,
        connector: config.connectors[0],
      });
    }
    signMessage({ message: "Hello from Frames v2!" });
  }, [connectAsync, isConnected, signMessage]);

  return (
    <>
      <BigPurpleButton
        onClick={handleSignMessage}
        disabled={isSignPending}
        isLoading={isSignPending}
      >
        Sign Message
      </BigPurpleButton>
      {isSignError && renderError(signError)}
      {signature && (
        <div className="mt-2 text-xs">
          <div>Signature: {signature}</div>
        </div>
      )}
    </>
  );
}

/**
 * SendEth Component
 */
function SendEth() {
  const { isConnected, chainId } = useAccount();
  const {
    sendTransaction,
    data,
    error: sendTxError,
    isError: isSendTxError,
    isPending: isSendTxPending,
  } = useSendTransaction();

  const { isLoading: isConfirming, isSuccess: isConfirmed } =
    useWaitForTransactionReceipt({
      hash: data,
    });

  const toAddr = useMemo(() => {
    // Example fallback addresses
    return chainId === base.id
      ? "0x32e3C7fD24e175701A35c224f2238d18439C7dBC"
      : "0xB3d8d7887693a9852734b4D25e9C0Bb35Ba8a830";
  }, [chainId]);

  const handleSend = useCallback(() => {
    sendTransaction({
      to: toAddr,
      value: 1n,
    });
  }, [toAddr, sendTransaction]);

  return (
    <>
      <BigPurpleButton
        onClick={handleSend}
        disabled={!isConnected || isSendTxPending}
        isLoading={isSendTxPending}
      >
        Send Transaction (eth)
      </BigPurpleButton>
      {isSendTxError && renderError(sendTxError)}
      {data && (
        <div className="mt-2 text-xs">
          <div>Hash: {truncateAddress(data)}</div>
          <div>
            Status:{" "}
            {isConfirming
              ? "Confirming..."
              : isConfirmed
              ? "Confirmed!"
              : "Pending"}
          </div>
        </div>
      )}
    </>
  );
}

const DebugView = () => {
  const { context, isFramePinned, notificationDetails, lastEvent } =
    useFrameSDK();
  const [isContextOpen, setIsContextOpen] = useState(false);
  const [txHash, setTxHash] = useState<string | null>(null);
  const [sendNotificationResult, setSendNotificationResult] = useState("");
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(
    null
  );

  const { address, isConnected } = useAccount();
  const chainId = useChainId();

  const {
    sendTransaction,
    error: sendTxError,
    isError: isSendTxError,
    isPending: isSendTxPending,
  } = useSendTransaction();

  const { isLoading: isConfirming, isSuccess: isConfirmed } =
    useWaitForTransactionReceipt({
      hash: txHash as `0x${string}`,
    });

  const {
    signTypedData,
    error: signTypedError,
    isError: isSignTypedError,
    isPending: isSignTypedPending,
  } = useSignTypedData();

  const { disconnect } = useDisconnect();
  const { connect } = useConnect();

  /**
   * Additional helpers
   */
  const openUrl = useCallback(() => {
    sdk.actions.openUrl("https://www.youtube.com/watch?v=dQw4w9WgXcQ");
  }, []);

  const openWarpcastUrl = useCallback(() => {
    sdk.actions.openUrl("https://warpcast.com/~/compose");
  }, []);

  const close = useCallback(() => {
    sdk.actions.close();
  }, []);

  const sendNotification = useCallback(async () => {
    setSendNotificationResult("");
    if (!notificationDetails || !context) {
      return;
    }

    try {
      const response = await fetch("/api/send-notification", {
        method: "POST",
        mode: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fid: context.user.fid,
          notificationDetails,
        }),
      });

      if (response.status === 200) {
        setSendNotificationResult("Success");
        return;
      } else if (response.status === 429) {
        setSendNotificationResult("Rate limited");
        return;
      }

      const data = await response.text();
      setSendNotificationResult(`Error: ${data}`);
    } catch (error) {
      setSendNotificationResult(`Error: ${error}`);
    }
  }, [context, notificationDetails]);

  const sendTx = useCallback(() => {
    sendTransaction(
      {
        // call yoink() on Yoink contract
        to: "0x4bBFD120d9f352A0BEd7a014bd67913a2007a878",
        data: "0x9846cd9efc000023c0",
      },
      {
        onSuccess: (hash) => {
          setTxHash(hash);
        },
      }
    );
  }, [sendTransaction]);

  const signTyped = useCallback(() => {
    signTypedData({
      domain: {
        name: "Frames v2 Demo",
        version: "1",
        chainId,
      },
      types: {
        Message: [{ name: "content", type: "string" }],
      },
      message: {
        content: "Hello from Frames v2!",
      },
      primaryType: "Message",
    });
  }, [chainId, signTypedData]);

  const toggleContext = useCallback(() => {
    setIsContextOpen((prev) => !prev);
  }, []);

  return (
    <div>
      <div className="mb-4">
        <h2 className="font-2xl font-bold">Context</h2>
        <BigPurpleButton
          onClick={toggleContext}
          className="flex items-center gap-2 transition-colors"
        >
          <span
            className={`transform transition-transform ${
              isContextOpen ? "rotate-90" : ""
            }`}
          >
            ➤
          </span>
          Tap to expand
        </BigPurpleButton>

        {isContextOpen && (
          <div className="p-4 mt-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
            <pre className="font-mono text-xs whitespace-pre-wrap break-words max-w-[260px] overflow-x-">
              {JSON.stringify(context, null, 2)}
            </pre>
          </div>
        )}
      </div>

      <div>
        <h2 className="font-2xl font-bold">Actions</h2>

        <div className="mb-4">
          <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg my-2">
            <pre className="font-mono text-xs whitespace-pre-wrap break-words max-w-[260px] overflow-x-">
              sdk.actions.openUrl
            </pre>
          </div>
          <BigPurpleButton onClick={openUrl}>Open Link</BigPurpleButton>
        </div>

        <div className="mb-4">
          <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg my-2">
            <pre className="font-mono text-xs whitespace-pre-wrap break-words max-w-[260px] overflow-x-">
              sdk.actions.openUrl
            </pre>
          </div>
          <BigPurpleButton onClick={openWarpcastUrl}>
            Open Warpcast Link
          </BigPurpleButton>
        </div>

        <div className="mb-4">
          <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg my-2">
            <pre className="font-mono text-xs whitespace-pre-wrap break-words max-w-[260px] overflow-x-">
              sdk.actions.close
            </pre>
          </div>
          <BigPurpleButton onClick={close}>Close Frame</BigPurpleButton>
        </div>
      </div>

      <div className="mb-4">
        <h2 className="font-2xl font-bold">Last event</h2>

        <div className="p-4 mt-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <pre className="font-mono text-xs whitespace-pre-wrap break-words max-w-[260px] overflow-x-">
            {lastEvent || "none"}
          </pre>
        </div>
      </div>

      <div>
        <h2 className="font-2xl font-bold">Add to client & notifications</h2>

        <div className="mt-2 mb-4 text-sm">
          Client fid {context?.client.clientFid},{" "}
          {isFramePinned
            ? " frame added to client,"
            : " frame not added to client,"}
          {notificationDetails
            ? " notifications enabled"
            : " notifications disabled"}
        </div>

        {sendNotificationResult && (
          <div className="mb-2 text-sm">
            Send notification result: {sendNotificationResult}
          </div>
        )}
        <div className="mb-4">
          <BigPurpleButton
            onClick={sendNotification}
            disabled={!notificationDetails}
          >
            Send notification
          </BigPurpleButton>
        </div>
      </div>

      <div>
        <h2 className="font-2xl font-bold">Wallet</h2>

        {address && (
          <div className="my-2 text-xs">
            Address: <pre className="inline">{truncateAddress(address)}</pre>
          </div>
        )}

        {chainId && (
          <div className="my-2 text-xs">
            Chain ID: <pre className="inline">{chainId}</pre>
          </div>
        )}

        <div className="mb-4">
          <BigPurpleButton
            onClick={() =>
              isConnected
                ? disconnect()
                : connect({ connector: config.connectors[0] })
            }
          >
            {isConnected ? "Disconnect" : "Connect"}
          </BigPurpleButton>
        </div>

        <div className="mb-4">
          <SignMessage />
        </div>

        {isConnected && (
          <>
            <div className="mb-4">
              <SendEth />
            </div>
            <div className="mb-4">
              <BigPurpleButton
                onClick={sendTx}
                disabled={!isConnected || isSendTxPending}
                isLoading={isSendTxPending}
              >
                Send Transaction (contract)
              </BigPurpleButton>
              {isSendTxError && renderError(sendTxError)}
              {txHash && (
                <div className="mt-2 text-xs">
                  <div>Hash: {truncateAddress(txHash)}</div>
                  <div>
                    Status:{" "}
                    {isConfirming
                      ? "Confirming..."
                      : isConfirmed
                      ? "Confirmed!"
                      : "Pending"}
                  </div>
                </div>
              )}
            </div>
            <div className="mb-4">
              <BigPurpleButton
                onClick={signTyped}
                disabled={!isConnected || isSignTypedPending}
                isLoading={isSignTypedPending}
              >
                Sign Typed Data
              </BigPurpleButton>
              {isSignTypedError && renderError(signTypedError)}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

/**
 * Simple Error Renderer
 */
const renderError = (error: Error | null) => {
  if (!error) return null;
  if (error instanceof BaseError) {
    const isUserRejection = error.walk(
      (e) => e instanceof UserRejectedRequestError
    );
    if (isUserRejection) {
      return <div className="text-red-500 text-xs mt-1">Rejected by user.</div>;
    }
  }
  return <div className="text-red-500 text-xs mt-1">{error.message}</div>;
};
