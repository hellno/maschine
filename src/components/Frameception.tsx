"use client";

import { useEffect, useCallback, useState, useMemo } from "react";
import { useMobileTheme } from "~/hooks/useMobileTheme";
import { AccessCheck } from "./AccessCheck";
import { ProjectOverviewCard } from "./ProjectOverviewCard";
import { ProjectDetailView } from "./ProjectDetailView";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "~/components/ui/tabs";
import { Card, CardContent } from "~/components/ui/card";
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
import { Project } from "~/lib/types";

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
  | "checkingAccess"
  | "enteringPrompt"
  | "pending"
  | "success";

export default function Frameception() {
  useMobileTheme();
  const [isSDKLoaded, setIsSDKLoaded] = useState(false);
  const [context, setContext] = useState<FrameContext>();
  const [isContextOpen, setIsContextOpen] = useState(false);
  const [txHash, setTxHash] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState("create_project");

  const [isFramePinned, setIsFramePinned] = useState(false);
  const [notificationDetails, setNotificationDetails] =
    useState<FrameNotificationDetails | null>(null);

  const [lastEvent, setLastEvent] = useState("");
  const [flowState, setFlowState] = useState<FlowState>("checkingAccess");
  const [addFrameResult, setAddFrameResult] = useState("");
  const [sendNotificationResult, setSendNotificationResult] = useState("");
  const [inputValue, setInputValue] = useState("");
  const [creationError, setCreationError] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(
    null
  );
  const [newProjectId, setNewProjectId] = useState<string | null>(null);

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

  const fetchProjects = useCallback(async () => {
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
  }, [context?.user?.fid]);

  const handleCreateProject = useCallback(async () => {
    try {
      if (inputValue.trim().length < 25) {
        throw new Error("Please enter at least 25 characters");
      }
      if (!context?.user?.fid) {
        throw new Error("User session not found");
      }

      setFlowState("pending");
      setCreationError(null);

      const response = await fetch("/api/new-frame-project", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: inputValue,
          userContext: context?.user,
        }),
      });
      if (!response.ok) {
        throw new Error("Failed to create project");
      }

      const responseData = await response.json();
      console.log("create frame project responseData", responseData);
      const projectId = responseData.project_id;
      setNewProjectId(projectId);
      setSelectedProjectId(projectId);
      setFlowState("success");
      await fetchProjects();
      requestAnimationFrame(() => {
        const detailView = document.getElementById("project-detail-view");
        if (detailView) {
          detailView.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
    } catch (error) {
      console.error("Error creating project:", error);
      setCreationError(
        error instanceof Error ? error.message : "An unknown error occurred"
      );
      setFlowState("enteringPrompt");
    }
  }, [inputValue, context?.user, fetchProjects]);

  useEffect(() => {
    setNotificationDetails(context?.client.notificationDetails ?? null);
  }, [context]);

  useEffect(() => {
    fetchProjects();
  }, [context?.user?.fid, fetchProjects]);

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
    if (flowState === "checkingAccess") {
      return (
        <AccessCheck
          userContext={context?.user}
          onAccessGranted={() => setFlowState("waitForFrameToBePinned")}
        />
      );
    }
    return (
      <>
        <Tabs
          defaultValue="create_project"
          className="w-full pt-8"
          value={activeTab}
          onValueChange={(value) => {
            setActiveTab(value);
            if (value === "view_projects") {
              fetchProjects();
            }
          }}
        >
          <TabsList className="grid w-full grid-cols-2 mb-6">
            <TabsTrigger value="create_project">New Project</TabsTrigger>
            <TabsTrigger
              value="view_projects"
              onClick={() => {
                setSelectedProjectId(null);
                fetchProjects();
              }}
            >
              My Frames
            </TabsTrigger>
          </TabsList>

          <TabsContent value="create_project">
            <div className="space-y-6">
              <Card className="border-0 shadow-lg">
                <CardContent className="pt-6">
                  <div className="space-y-6">
                    <div className="relative">
                      <div className="flex justify-between items-center mb-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                          Describe your frame
                        </label>
                        <span className="text-sm text-gray-500">
                          {inputValue.length}/25
                        </span>
                      </div>
                      <textarea
                        rows={5}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Create a quiz game about crypto trends with 5 multiple choice questions"
                        className="w-full p-4 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100"
                      />
                      <p className="text-sm text-gray-500 mt-2 text-left">
                        Describe your frame in at least 25 characters. The more
                        detail you provide, the better the frame will be. You
                        can keep chatting with the AI later to improve your
                        frame.
                      </p>
                    </div>

                    <Button
                      size="lg"
                      className="w-full py-4 text-lg font-semibold"
                      onClick={handleCreateProject}
                      disabled={
                        inputValue.trim().length < 25 || flowState === "pending"
                      }
                    >
                      {flowState === "pending" ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Creating Project...
                        </>
                      ) : (
                        "Start Building →"
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <div className="mt-8">
                <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-4 uppercase tracking-wide">
                  Popular Starting Points
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {promptTemplates.map((template) => (
                    <button
                      key={template.title}
                      onClick={() => setInputValue(template.template)}
                      className="group p-4 text-left rounded-xl border hover:border-blue-500 dark:border-gray-700 dark:hover:border-blue-600 transition-all bg-white dark:bg-gray-800 hover:shadow-sm"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-gray-900 dark:text-gray-100">
                          {template.title}
                        </span>
                        <ArrowUp className="w-4 h-4 text-gray-400 group-hover:text-blue-500 transition-colors transform rotate-45" />
                      </div>
                      <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                        {template.template}
                      </p>
                    </button>
                  ))}
                </div>
              </div>

              {creationError && (
                <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-xl text-red-600 dark:text-red-400 flex items-center">
                  <AlertCircle className="w-5 h-5 mr-2" />
                  {creationError}
                </div>
              )}

              {(flowState === "pending" || flowState === "success") &&
                newProjectId && (
                  <div
                    id="project-detail-view"
                    className="flex flex-col items-center gap-4 w-full max-w-3xl mx-auto px-4 scroll-target"
                  >
                    <ProjectDetailView
                      projectId={newProjectId}
                      userContext={context?.user}
                    />
                  </div>
                )}
            </div>
          </TabsContent>

          <TabsContent value="view_projects">
            {selectedProjectId ? (
              <div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSelectedProjectId(null);
                    fetchProjects();
                  }}
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
                    key={project.id}
                    project={project}
                    onClick={() => setSelectedProjectId(project.id)}
                  />
                ))}
                {projects.length === 0 && (
                  <div className="text-center text-gray-500 py-8">
                    No projects yet. Create your first project in the Create
                    tab!
                  </div>
                )}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </>
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
      <div className="mx-auto py-2 px-2 md:px-4 max-w-3xl text-center">
        <div className="mx-auto max-w-3xl lg:pt-8">
          <div className="mt-8 flex justify-center">
            <img
              alt="Frameception Logo"
              src="/icon.png"
              className="h-20 w-20 rounded-xl"
            />
          </div>
          <h1 className="mx-auto mt-4 text-pretty text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl md:text-6xl dark:text-gray-100 max-w-xl">
            Create your own Farcaster frame <br className="hidden md:inline" />
            {context?.user && (
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                in a Farcaster frame
              </span>
            )}
          </h1>
          <div className="mt-4 sm:mt-8 lg:mt-10">
            <div className="flex justify-center space-x-4">
              <span className="rounded-full bg-blue-600/10 px-3 py-1 text-sm/6 font-semibold text-blue-600 ring-1 ring-inset ring-blue-600/10 dark:bg-blue-400/20 dark:text-blue-300 dark:ring-blue-400/30">
                What&apos;s new
              </span>
              <Sheet>
                <SheetTrigger className="inline-flex items-center space-x-2 text-sm/6 font-medium text-gray-600 hover:text-blue-600 dark:text-gray-300 dark:hover:text-blue-400 transition-colors">
                  <PlayCircle className="w-4 h-4" />
                  <span>Watch v0.1 Demo</span>
                </SheetTrigger>
                <SheetContent className="w-full max-w-4xl sm:max-w-6xl">
                  <SheetHeader>
                    <SheetTitle>Frameception Demo</SheetTitle>
                  </SheetHeader>
                  <div
                    className="relative mt-4"
                    style={{ paddingTop: "56.25%" }}
                  >
                    <iframe
                      src="https://player.vimeo.com/video/1047553467?h=af29b86b8e&badge=0&autopause=0&player_id=0&app_id=58479"
                      allow="autoplay; fullscreen; picture-in-picture; clipboard-write; encrypted-media; presentation"
                      className="absolute top-0 left-0 w-full h-full rounded-lg"
                      title="frameception-demo"
                    />
                  </div>
                </SheetContent>
              </Sheet>
            </div>
          </div>
          {/* <p className="mt-6 mx-8 text-pretty text-lg font-medium text-gray-600 sm:text-xl/8 dark:text-gray-400 max-w-2xl">
            From idea to live frame to share with the world. Create your own
            Farcaster frame right here.
          </p> */}
        </div>

        {renderMainContent()}

        {creationError && (
          <div className="text-red-500 font-bold mt-2 text-center">
            Error: {creationError}
          </div>
        )}
        {process.env.NEXT_PUBLIC_URL?.endsWith("cloudflare.com") && (
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
              <h2 className="font-2xl font-bold">
                Add to client & notifications
              </h2>

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
                  Address:{" "}
                  <pre className="inline">{truncateAddress(address)}</pre>
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
