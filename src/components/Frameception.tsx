"use client";

import { useEffect, useCallback, useState, useMemo } from "react";
import { ProjectOverviewCard } from "./ProjectOverviewCard";
import { ProjectDetailView } from "./ProjectDetailView";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "~/components/ui/tabs";
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
import { BigPurpleButton } from "~/components/ui/BigPurpleButton";
import { truncateAddress } from "~/lib/truncateAddress";
import { base } from "wagmi/chains";
import { Button } from "./ui/Button";
import { ArrowBigUp, ArrowUp } from "lucide-react";

const promptTemplates = [
  {
    title: "Link Tree",
    template:
      "Create a link tree frame that shows my social links and allows users to navigate between them. Include links to: Farcaster, GitHub, and other links I've shared recently.",
  },
  {
    title: "Image Gallery",
    template:
      "Create a frame that shows a gallery of images with next/previous navigation. Include 5 images or videos that I have shared recently.",
  },
  {
    title: "Quiz Game",
    template:
      "Make a multiple choice quiz game frame based on my recent casts. Include 2 questions with 4 options each and show the score at the end.",
  },
  {
    title: "Event Countdown",
    template:
      "Show a countdown timer for my event coming up at 5pm on Friday UTC.",
  },
];

type FlowState =
  | "waitForFrameToBePinned"
  | "enteringPrompt"
  | "pending"
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
  const [flowState, setFlowState] = useState<FlowState>(
    "waitForFrameToBePinned"
  );

  const [addFrameResult, setAddFrameResult] = useState("");
  const [sendNotificationResult, setSendNotificationResult] = useState("");
  const [inputValue, setInputValue] = useState("");
  const [creationError, setCreationError] = useState<string | null>(null);
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(
    null
  );

  console.log('context',context)

  const handleCreateProject = useCallback(async () => {
    try {
      setFlowState("pending");
      setCreationError(null);

      if (!context?.user?.fid) {
        throw new Error("User FID is required");
      }

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

      const { projectId } = await response.json();
      setSelectedProjectId(projectId);
    } catch (error) {
      console.error("Error creating project:", error);
      setCreationError(
        error instanceof Error ? error.message : "An unknown error occurred"
      );
      setFlowState("enteringPrompt");
    }
  }, [inputValue, context?.user]);

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

  const renderMainContent = () => {
    if (false && !isFramePinned) {
      return (
        <div className="my-20">
          <h2 className="font-5xl font-bold mb-2">
            Hey {context?.user.username}, bookmark this to start building your
            frame
          </h2>
          <h3 className="font-2xl mb-4 text-gray-600">
            We will notify you when your frame is ready!
          </h3>
          <BigPurpleButton
            className="flex justify-center items-center gap-2"
            onClick={async () => {
              addFrame().then(() => setFlowState("enteringPrompt"));
            }}
          >
            Get Started
          </BigPurpleButton>
        </div>
      );
    }

    return (
      <Tabs defaultValue="create_project" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="create_project">New</TabsTrigger>
          <TabsTrigger
            value="view_projects"
            onClick={() => setSelectedProjectId(null)}
          >
            View Projects
          </TabsTrigger>
        </TabsList>

        <TabsContent value="create_project">
          <Card className="">
            <CardHeader>
              <CardTitle>
                Hey @{context?.user.username}, what frame would you like to
                build?
              </CardTitle>
              <CardDescription>
                Enter a prompt to start your new frame project.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col gap-2">
                <textarea
                  rows={5}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="linktree for me with the following link..."
                  className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <BigPurpleButton
                  className="flex items-center justify-center gap-2"
                  onClick={handleCreateProject}
                  disabled={!inputValue.trim()}
                >
                  Let&apos;s build it
                  <ArrowUp className="w-4 h-4" />
                </BigPurpleButton>
                <div className="mt-4">
                  <p className="text-sm text-gray-500 mb-2">
                    Or try one of these templates:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {promptTemplates.map((template, index) => (
                      <button
                        key={index}
                        onClick={() => setInputValue(template.template)}
                        className="inline-flex items-center gap-1 px-3 py-1 text-xs font-medium 
                                 rounded-full border border-gray-200 bg-gray-50 text-gray-700
                                 hover:bg-gray-100 hover:border-gray-300 transition-colors
                                 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500"
                      >
                        {template.title}
                        <svg
                          width="12"
                          height="12"
                          viewBox="0 0 16 16"
                          fill="none"
                          stroke="currentColor"
                          className="ml-1"
                        >
                          <path
                            d="M6.75 4H6v1.5h.75 2.69L5.47 9.47l-.53.53L6 11.06l.53-.53 3.97-3.97v2.69V10h1.5V9.25V5c0-.55-.45-1-1-1H6.75z"
                            fill="currentColor"
                          />
                        </svg>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {(flowState === "pending" || flowState === "success") && (
            <div className="my-20 flex flex-col items-center gap-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
              <p className="text-center">Creating your frame...</p>
              {selectedProjectId && (
                <ProjectDetailView
                  projectId={selectedProjectId}
                  userContext={context?.user}
                />
              )}
            </div>
          )}
        </TabsContent>

        <TabsContent value="view_projects">
          {selectedProjectId ? (
            <div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedProjectId(null)}
                className="mb-4"
              >
                ← Back to Projects
              </Button>
              <ProjectDetailView
                projectId={selectedProjectId}
                userContext={context?.user}
              />
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {projects.map((project) => (
                <ProjectOverviewCard
                  key={project.projectId}
                  projectId={project.id}
                  name={
                    project?.repo_url?.split("frameception-v2/")[1] ||
                    project.id?.split("-")[0]
                  }
                  repoUrl={project.repo_url}
                  frontendUrl={project.frontend_url}
                  createdAt={project.created_at}
                  onClick={() => setSelectedProjectId(project.id)}
                />
              ))}
              {projects.length === 0 && (
                <div className="text-center text-gray-500 py-8">
                  No projects yet. Create your first project in the Create tab!
                </div>
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>
    );
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
      <div className="mx-auto py-2 px-8">
        <h1 className="text-2xl font-bold text-center mb-4">{title}</h1>

        {renderMainContent()}

        {creationError && (
          <div className="text-red-500 font-bold mt-2 text-center">
            Error: {creationError}
          </div>
        )}
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
            <BigPurpleButton onClick={addFrame} disabled={isFramePinned}>
              Add frame to client
            </BigPurpleButton>
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
        <BigPurpleButton onClick={handleSignIn} disabled={signingIn}>
          Sign In with Farcaster
        </BigPurpleButton>
      )}
      {status === "authenticated" && (
        <BigPurpleButton onClick={handleSignOut} disabled={signingOut}>
          Sign out
        </BigPurpleButton>
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
