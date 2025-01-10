"use client";

import { useEffect, useCallback, useState, useMemo } from "react";
import type { ProjectInfo } from "~/lib/kv";
import { signIn, signOut, getCsrfToken } from "next-auth/react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "~/components/ui/card";
import sdk, {
  FrameNotificationDetails,
  type FrameContext,
} from "@farcaster/frame-sdk";
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
import { useSession } from "next-auth/react";
import { SignIn as SignInCore } from "@farcaster/frame-core";
import { SignInResult } from "@farcaster/frame-core/dist/actions/signIn";

import { config } from "~/components/providers/WagmiProvider";
import { Button } from "~/components/ui/Button";
import { truncateAddress } from "~/lib/truncateAddress";
import { base } from "wagmi/chains";

type FlowState =
  | "initial"
  | "enteringPrompt"
  | "creatingProject"
  | "customizingTemplate"
  | "deploying"
  | "success";

export default function Frameception(
  { title }: { title?: string } = { title: "Frameception" }
) {
  const [isSDKLoaded, setIsSDKLoaded] = useState(false);
  const [context, setContext] = useState<FrameContext>();
  const [isContextOpen, setIsContextOpen] = useState(false);
  const [txHash, setTxHash] = useState<string | null>(null);

  const [isFramePinned, setIsFramePinned] = useState(false);
  const [notificationDetails, setNotificationDetails] =
    useState<FrameNotificationDetails | null>(null);

  const [lastEvent, setLastEvent] = useState("");
  const [flowState, setFlowState] = useState<FlowState>("initial");

  const [addFrameResult, setAddFrameResult] = useState("");
  const [sendNotificationResult, setSendNotificationResult] = useState("");
  const [inputValue, setInputValue] = useState("");
  const [repoPath, setRepoPath] = useState<string | null>(null);
  const [vercelUrl, setVercelUrl] = useState<string | null>(null);
  const [creationError, setCreationError] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(
    null
  );

  /**
   * 1) Single handleCustomizingTemplate definition
   */
  const handleCustomizingTemplate = useCallback(async () => {
    try {
      console.log("handleCustomizingTemplate called with", inputValue, context);
      if (!inputValue || !context || !repoPath) {
        throw new Error("Missing required data for template customization");
      }

      setCreationError(null);

      // Create a new job for template customization
      const response = await fetch("/api/customize-template", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: inputValue,
          userContext: context,
          repoPath,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to start template customization");
      }

      const { jobId } = await response.json();
      // Start polling the new job
      pollJobStatus(jobId);
    } catch (error) {
      console.error("Error customizing template:", error);
      setCreationError(
        error instanceof Error ? error.message : "Template customization failed"
      );
      setFlowState("enteringPrompt");
    }
  }, [inputValue, context, repoPath]);

  /**
   * 2) pollJobStatus references handleCustomizingTemplate
   */
  const pollJobStatus = useCallback(
    async (jobId: string) => {
      try {
        console.log("Polling job status:", jobId);
        const response = await fetch(`/api/job/${jobId}`);
        const data = await response.json();

        if (data.error) {
          setCreationError(data.error);
          return;
        }

        // Update logs as an array
        setLogs(data.logs || []);
        console.log("job data", data);

        // Continue polling if job is still in progress
        if (data.status === "in-progress" || data.status === "pending") {
          setTimeout(() => pollJobStatus(jobId), 2000);
        } else if (data.status === "completed") {
          console.log("Job completed:", data);
          setFlowState((prev) => {
            if (prev === "creatingProject") {
              handleCustomizingTemplate();
              return "customizingTemplate";
            } else if (prev === "customizingTemplate") {
              return "success";
            }
            return prev;
          });
        } else if (data.status === "failed") {
          setFlowState("enteringPrompt");
        }
      } catch (error) {
        setCreationError(
          error instanceof Error ? error.message : "Polling error"
        );
      }
    },
    [handleCustomizingTemplate]
  );

  /**
   * 3) handleCreateProject to create the first job
   */
  const handleCreateProject = useCallback(async () => {
    try {
      setFlowState("creatingProject");
      setCreationError(null);
      setRepoPath(null);

      if (!context?.user?.fid) {
        throw new Error("User FID is required");
      }

      // Create project (first job)
      const response = await fetch("/api/new-frame-project", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: inputValue,
          description: "A new Farcaster frame project",
          username: context?.user?.username || null,
          fid: context.user.fid,
          verbose: false,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to create project");
      }

      const { jobId } = await response.json();
      pollJobStatus(jobId);
    } catch (error) {
      console.error("Error creating project:", error);
      setCreationError(
        error instanceof Error ? error.message : "An unknown error occurred"
      );
      setFlowState("enteringPrompt");
    }
  }, [inputValue, context?.user?.username, pollJobStatus]);

  /**
   * React effects and setup
   */
  useEffect(() => {
    setNotificationDetails(context?.client.notificationDetails ?? null);
  }, [context]);

  useEffect(() => {
    const fetchProjects = async () => {
      if (context?.user?.fid) {
        try {
          const response = await fetch(`/api/projects?fid=${context.user.fid}`);
          const data = await response.json();
          if (data.projects) {
            setProjects(data.projects);
          }
        } catch (error) {
          console.error("Error fetching projects:", error);
        }
      }
    };

    fetchProjects();
  }, [context?.user?.fid]);

  useEffect(() => {
    if (isFramePinned) {
      setFlowState("enteringPrompt");
    }
  }, [isFramePinned]);

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

  useEffect(() => {
    const load = async () => {
      const frameContext = await sdk.context;
      if (!frameContext) {
        return;
      }

      setContext(frameContext);
      setIsFramePinned(frameContext.client.added);

      sdk.on("frameAdded", ({ notificationDetails }) => {
        setLastEvent(
          `frameAdded${notificationDetails ? ", notifications enabled" : ""}`
        );

        setIsFramePinned(true);
        if (notificationDetails) {
          setNotificationDetails(notificationDetails);
        }
      });

      sdk.on("frameAddRejected", ({ reason }) => {
        setLastEvent(`frameAddRejected, reason ${reason}`);
      });

      sdk.on("frameRemoved", () => {
        setLastEvent("frameRemoved");
        setIsFramePinned(false);
        setNotificationDetails(null);
      });

      sdk.on("notificationsEnabled", ({ notificationDetails }) => {
        setLastEvent("notificationsEnabled");
        setNotificationDetails(notificationDetails);
      });
      sdk.on("notificationsDisabled", () => {
        setLastEvent("notificationsDisabled");
        setNotificationDetails(null);
      });

      sdk.on("primaryButtonClicked", () => {
        console.log("primaryButtonClicked");
      });

      sdk.actions.ready({});
    };
    if (sdk && !isSDKLoaded) {
      setIsSDKLoaded(true);
      load();
      return () => {
        sdk.removeAllListeners();
      };
    }
  }, [isSDKLoaded]);

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

  const addFrame = useCallback(async () => {
    try {
      setNotificationDetails(null);

      const result = await sdk.actions.addFrame();
      console.log("addFrame result", result);
      if (result.added) {
        if (result.notificationDetails) {
          setNotificationDetails(result.notificationDetails);
        }
        setAddFrameResult(
          result.notificationDetails
            ? `Added, got notificaton token ${result.notificationDetails.token} and url ${result.notificationDetails.url}`
            : "Added, got no notification details"
        );
      } else {
        setAddFrameResult(`Not added: ${result.reason}`);
      }
    } catch (error) {
      setAddFrameResult(`Error: ${error}`);
    }
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

  if (!isSDKLoaded) {
    return <div>Loading...</div>;
  }

  /**
   * Main UI flow
   */
  const renderMainContent = () => {
    switch (flowState) {
      case "initial":
        return (
          <div className="my-20">
            <h2 className="font-5xl font-bold mb-2">
              Hey {context?.user.username}, bookmark this to start building your
              frame
            </h2>
            <h3 className="font-2xl mb-4 text-gray-600">
              We will notify in Warpcast when your frame is ready to use!
            </h3>
            <Button
              onClick={async () => {
                addFrame().then(() => setFlowState("enteringPrompt"));
              }}
            >
              Get Started
            </Button>
          </div>
        );

      case "enteringPrompt":
        return (
          <div className="my-20">
            <h2 className="font-5xl font-bold mb-2">
              {context?.user.username}, what kind of frame can I help you build?
            </h2>
            <div className="flex flex-col gap-2">
              <textarea
                rows={5}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="linktree for me with the following link..."
                className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <Button
                onClick={async () => {
                  setFlowState("creatingProject");
                  await handleCreateProject();
                }}
                disabled={!inputValue.trim()}
              >
                Let&apos;s go
              </Button>

              {projects.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold mb-2">Past Projects</h3>
                  <div className="grid grid-cols-1 gap-4">
                    {projects.map((project) => (
                      <Card
                        key={project.projectId}
                        className={`transition-colors ${
                          selectedProjectId === project.projectId
                            ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                            : "hover:border-gray-400"
                        }`}
                        onClick={() => setSelectedProjectId(project.projectId)}
                      >
                        <CardHeader className="pb-2">
                          <CardTitle className="text-base">
                            {project.repoUrl.split("frameception-v2/")[1]}
                          </CardTitle>
                          <CardDescription className="text-xs">
                            Created{" "}
                            {new Date(project.createdAt).toLocaleDateString()}
                          </CardDescription>
                        </CardHeader>
                        <CardFooter className="pt-2">
                          <div className="flex gap-3 text-sm">
                            {project.repoUrl && (
                              <a
                                href={project.repoUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-500 hover:text-blue-700 hover:underline"
                                onClick={(e) => e.stopPropagation()}
                              >
                                GitHub
                              </a>
                            )}
                            {project.vercelUrl && (
                              <a
                                href={project.vercelUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-500 hover:text-blue-700 hover:underline"
                                onClick={(e) => e.stopPropagation()}
                              >
                                Live Demo
                              </a>
                            )}
                          </div>
                        </CardFooter>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        );

      case "creatingProject":
        return (
          <div className="my-20 flex flex-col items-center gap-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
            <p className="text-center">
              going deep into the frameception for you...
            </p>
            <div className="w-full max-h-48 overflow-y-auto bg-gray-50 rounded-lg p-4">
              <pre className="text-sm text-gray-600 whitespace-pre-wrap">
                {logs ? logs.join("\n") : "Waiting for logs..."}
              </pre>
            </div>
            {/* Debug section */}
            <div className="flex flex-col gap-2 w-full max-w-xs">
              <Button
                onClick={() => {
                  const urlParams = new URLSearchParams(window.location.search);
                  const jobId = urlParams.get("jobId");
                  if (jobId) {
                    console.log(
                      "Manually restarting polling for jobId:",
                      jobId
                    );
                    pollJobStatus(jobId);
                  } else {
                    console.error("No jobId found in URL parameters");
                  }
                }}
                variant="outline"
                size="sm"
              >
                Debug: Restart Polling
              </Button>

              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Enter Job ID manually"
                  className="flex-1 px-3 py-1 text-sm border rounded-md"
                  onChange={(e) => {
                    const jobId = e.target.value.trim();
                    if (jobId) {
                      console.log("Manual jobId entered:", jobId);
                      pollJobStatus(jobId);
                    }
                  }}
                />
              </div>
            </div>
          </div>
        );

      case "customizingTemplate":
        return (
          <div className="my-20 flex flex-col items-center gap-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
            <p className="text-center">
              LLMs are carefully working on your frame...
            </p>
            <div className="w-full max-h-48 overflow-y-auto bg-gray-50 rounded-lg p-4">
              <pre className="text-sm text-gray-600 whitespace-pre-wrap">
                {logs ? logs.join("\n") : "Waiting for logs..."}
              </pre>
            </div>
          </div>
        );

      case "deploying":
        return (
          <div className="my-20 flex flex-col items-center gap-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
            <p className="text-center">Deploying your frame...</p>
            <p className="text-sm text-gray-600">Setting up Vercel project</p>
          </div>
        );

      case "success":
        return (
          <div className="my-20">
            <h2 className="font-5xl font-bold mb-2">Your frame is ready!</h2>
            <div className="flex flex-col gap-2">
              {repoPath && (
                <a
                  href={repoPath}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-500 hover:text-blue-700 text-sm text-center"
                >
                  View your new repository on GitHub
                </a>
              )}
              {vercelUrl && (
                <a
                  href={vercelUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-500 hover:text-blue-700 text-sm text-center"
                >
                  View your live deployment on Vercel
                </a>
              )}
            </div>
          </div>
        );
    }
  };

  return (
    <div
      style={{
        paddingTop: context?.client.safeAreaInsets?.top ?? 0,
        paddingBottom: context?.client.safeAreaInsets?.bottom ?? 0,
        paddingLeft: context?.client.safeAreaInsets?.left ?? 0,
        paddingRight: context?.client.safeAreaInsets?.right ?? 0,
      }}
    >
      <div className="w-[300px] mx-auto py-2 px-2">
        <h1 className="text-2xl font-bold text-center mb-4">{title}</h1>

        {renderMainContent()}

        {creationError && (
          <div className="text-red-500 font-bold mt-2 text-center">
            Error: {creationError}
          </div>
        )}
        <div className="mb-4">
          <h2 className="font-2xl font-bold">Context</h2>
          <button
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
          </button>

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
                sdk.actions.signIn
              </pre>
            </div>
            <SignIn />
          </div>

          <div className="mb-4">
            <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg my-2">
              <pre className="font-mono text-xs whitespace-pre-wrap break-words max-w-[260px] overflow-x-">
                sdk.actions.openUrl
              </pre>
            </div>
            <Button onClick={openUrl}>Open Link</Button>
          </div>

          <div className="mb-4">
            <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg my-2">
              <pre className="font-mono text-xs whitespace-pre-wrap break-words max-w-[260px] overflow-x-">
                sdk.actions.openUrl
              </pre>
            </div>
            <Button onClick={openWarpcastUrl}>Open Warpcast Link</Button>
          </div>

          <div className="mb-4">
            <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg my-2">
              <pre className="font-mono text-xs whitespace-pre-wrap break-words max-w-[260px] overflow-x-">
                sdk.actions.close
              </pre>
            </div>
            <Button onClick={close}>Close Frame</Button>
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

          <div className="mb-4">
            <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg my-2">
              <pre className="font-mono text-xs whitespace-pre-wrap break-words max-w-[260px] overflow-x-">
                sdk.actions.addFrame
              </pre>
            </div>
            {addFrameResult && (
              <div className="mb-2 text-sm">
                Add frame result: {addFrameResult}
              </div>
            )}
            <Button onClick={addFrame} disabled={isFramePinned}>
              Add frame to client
            </Button>
          </div>

          {sendNotificationResult && (
            <div className="mb-2 text-sm">
              Send notification result: {sendNotificationResult}
            </div>
          )}
          <div className="mb-4">
            <Button onClick={sendNotification} disabled={!notificationDetails}>
              Send notification
            </Button>
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
            <Button
              onClick={() =>
                isConnected
                  ? disconnect()
                  : connect({ connector: config.connectors[0] })
              }
            >
              {isConnected ? "Disconnect" : "Connect"}
            </Button>
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
                <Button
                  onClick={sendTx}
                  disabled={!isConnected || isSendTxPending}
                  isLoading={isSendTxPending}
                >
                  Send Transaction (contract)
                </Button>
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
                <Button
                  onClick={signTyped}
                  disabled={!isConnected || isSignTypedPending}
                  isLoading={isSignTypedPending}
                >
                  Sign Typed Data
                </Button>
                {isSignTypedError && renderError(signTypedError)}
              </div>
            </>
          )}
        </div>
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
      <Button
        onClick={handleSignMessage}
        disabled={isSignPending}
        isLoading={isSignPending}
      >
        Sign Message
      </Button>
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
      <Button
        onClick={handleSend}
        disabled={!isConnected || isSendTxPending}
        isLoading={isSendTxPending}
      >
        Send Transaction (eth)
      </Button>
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

/**
 * SignIn Component
 */
function SignIn() {
  const [signingIn, setSigningIn] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const [signInResult, setSignInResult] = useState<SignInResult>();
  const [signInFailure, setSignInFailure] = useState<string>();
  const { data: session, status } = useSession();

  const getNonce = useCallback(async () => {
    const nonce = await getCsrfToken();
    if (!nonce) throw new Error("Unable to generate nonce");
    return nonce;
  }, []);

  const handleSignIn = useCallback(async () => {
    try {
      setSigningIn(true);
      setSignInFailure(undefined);
      const nonce = await getNonce();
      const result = await sdk.actions.signIn({ nonce });
      setSignInResult(result);

      await signIn("credentials", {
        message: result.message,
        signature: result.signature,
        redirect: false,
      });
    } catch (e) {
      if (e instanceof SignInCore.RejectedByUser) {
        setSignInFailure("Rejected by user");
        return;
      }
      setSignInFailure("Unknown error");
    } finally {
      setSigningIn(false);
    }
  }, [getNonce]);

  const handleSignOut = useCallback(async () => {
    try {
      setSigningOut(true);
      await signOut({ redirect: false });
      setSignInResult(undefined);
    } finally {
      setSigningOut(false);
    }
  }, []);

  return (
    <>
      {status !== "authenticated" && (
        <Button onClick={handleSignIn} disabled={signingIn}>
          Sign In with Farcaster
        </Button>
      )}
      {status === "authenticated" && (
        <Button onClick={handleSignOut} disabled={signingOut}>
          Sign out
        </Button>
      )}
      {session && (
        <div className="my-2 p-2 text-xs overflow-x-scroll bg-gray-100 rounded-lg font-mono">
          <div className="font-semibold text-gray-500 mb-1">Session</div>
          <div className="whitespace-pre">
            {JSON.stringify(session, null, 2)}
          </div>
        </div>
      )}
      {signInFailure && !signingIn && (
        <div className="my-2 p-2 text-xs overflow-x-scroll bg-gray-100 rounded-lg font-mono">
          <div className="font-semibold text-gray-500 mb-1">SIWF Result</div>
          <div className="whitespace-pre">{signInFailure}</div>
        </div>
      )}
      {signInResult && !signingIn && (
        <div className="my-2 p-2 text-xs overflow-x-scroll bg-gray-100 rounded-lg font-mono">
          <div className="font-semibold text-gray-500 mb-1">SIWF Result</div>
          <div className="whitespace-pre">
            {JSON.stringify(signInResult, null, 2)}
          </div>
        </div>
      )}
    </>
  );
}

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
