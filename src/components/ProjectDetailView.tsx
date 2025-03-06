"use client";

import { useEffect, useState, useCallback } from "react";
import {
  GitBranch,
  Share,
  ExternalLink,
  Copy,
  CircleXIcon,
  LoaderCircle,
  CheckCircle,
  EllipsisVertical,
} from "lucide-react";
import { Button } from "./ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";
import sdk from "@farcaster/frame-sdk";
import { Log, Project } from "~/lib/types";
import Link from "next/link";
import { useFrameSDK } from "~/hooks/useFrameSDK";
import ActivityLogCard from "./ActivityLog";
import ConversationCard from "./ConversationCard";
import UpdatePromptInput from "./UpdatePromptInput";
import FramePreviewCard from "./FramePreviewCard";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Label } from "./ui/label";
import { useProjects } from "~/hooks/useProjects";
import { useRouter } from "next/navigation";

const styles = {
  card: "bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700",
  cardHeader: "px-6 py-4 border-b border-gray-100 dark:border-gray-700",
  cardContent: "p-6",
  deploymentStatus: {
    ready: "text-green-600 bg-green-50 dark:bg-green-900/20",
    error: "text-red-600 bg-red-50 dark:bg-red-900/20",
    building: "text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20",
    pending: "text-blue-600 bg-blue-50 dark:bg-blue-900/20",
  },
  badge:
    "px-2.5 py-0.5 rounded-full text-xs font-medium inline-flex items-center gap-1",
  link: "text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 inline-flex items-center gap-2 transition-colors",
  chat: {
    userMessage: "bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg break-words",
    botMessage: "bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg break-words",
    timestamp: "text-xs text-gray-500 mt-1",
    container: "space-y-4",
  },
};

interface ProjectDetailViewProps {
  projectId: string | null;
}

function ProjectInfoCard({
  project,
  isSubmitting,
}: {
  project: Project;
  isSubmitting: boolean;
}) {
  const router = useRouter();
  const { context } = useFrameSDK();
  const { removeProject } = useProjects(context?.user?.fid);
  const handleCopyUrl = async () => {
    if (project.frontend_url) {
      try {
        await navigator.clipboard.writeText(project.frontend_url);
        console.log("URL copied to clipboard");
      } catch (err) {
        console.error("Failed to copy URL:", err);
      }
    }
  };

  const handleShare = () => {
    if (project.frontend_url) {
      const shareText = `Check out my frame "${project.name}" built with frameception`;
      const shareUrl = `https://warpcast.com/~/compose?text=${encodeURIComponent(
        shareText,
      )}&embeds[]=${encodeURIComponent(project.frontend_url)}`;
      sdk.actions.openUrl(shareUrl);
    }
  };

  const getProjectStatus = () => {
    if (!project) return {};
    if (!project.latestBuild && !project.latestJob) return {};

    const { latestBuild, latestJob } = project;
    const latestBuildStarted = latestBuild?.created_at
      ? new Date(latestBuild?.created_at)
      : new Date();
    const latestJobStarted = latestJob?.created_at
      ? new Date(latestJob?.created_at)
      : new Date();

    let text = "pending";
    let statusColor = "gray";
    let description = "";
    let icon = <LoaderCircle className="w-4 h-4 animate-spin" />;

    const isLatestJobDone =
      latestJob?.status !== "running" && latestJob?.status !== "failed";
    if (latestBuildStarted > latestJobStarted && isLatestJobDone) {
      const status = latestBuild?.status;
      switch (status) {
        case "submitted":
        case "queued":
        case "building":
          text = "building";
          statusColor = "blue";
          icon = <LoaderCircle className="w-4 h-4 animate-spin" />;
          description = "Maschine is pushing your changes to the live website";
          break;
        case "success":
          text = "ready";
          statusColor = "green";
          icon = <CheckCircle className="w-4 h-4" />;
          break;
        case "error":
          text = "error";
          statusColor = "red";
          icon = <CircleXIcon className="w-4 h-4" />;
          break;
      }
    } else {
      const status = project?.latestJob?.status;
      switch (status) {
        case "pending":
        case "running":
        case "completed":
          text = "building";
          statusColor = "blue";
          icon = <LoaderCircle className="w-4 h-4 animate-spin" />;
          description = "Maschine is writing code for you";
          break;
        case "failed":
          text = "error";
          statusColor = "red";
          icon = <CircleXIcon className="w-4 h-4" />;
          break;
      }
    }
    const statusComponent = (
      <div
        className={`flex items-center px-4 py-2 text-md font-medium rounded-full border border-${statusColor}-500 bg-${statusColor}-50 text-${statusColor}-600 dark:bg-${statusColor}-900 dark:text-${statusColor}-200 dark:border-${statusColor}-700`}
      >
        {icon && <span className="mr-2">{icon}</span>}
        {text}
      </div>
    );

    return {
      statusComponent,
      description,
    };
  };

  const renderDropdownMenu = () => (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon" className="h-10 w-10">
          <EllipsisVertical className="w-4 h-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuItem
          onClick={handleShare}
          className="transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <Share className="w-4 h-4 mr-2" />
          Share
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={handleCopyUrl}
          className="transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <Copy className="w-4 h-4 mr-2" />
          Copy URL
        </DropdownMenuItem>
        <DropdownMenuItem
          onSelect={(e) => e.preventDefault()} // Prevent immediate action
          className="transition-colors hover:bg-red-100 dark:hover:bg-red-900 text-red-600 dark:text-red-400"
        >
          <Dialog>
            <DialogTrigger className="w-full text-left flex items-center">
              <CircleXIcon className="w-4 h-4 mr-2" />
              Remove
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Remove {project.name}?</DialogTitle>
                <DialogDescription>
                  Are you sure you want to remove this project? This action
                  cannot be undone.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter className="gap-2">
                <Button
                  variant="outline"
                  onClick={() =>
                    document.dispatchEvent(
                      new KeyboardEvent("keydown", { key: "Escape" }),
                    )
                  }
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  disabled={!project?.id || removeProject.isPending}
                  onClick={() => {
                    if (removeProject && project?.id) {
                      removeProject.mutate(project.id);
                    }
                  }}
                >
                  {removeProject.isPending ? (
                    <LoaderCircle className="w-4 h-4 animate-spin mr-2" />
                  ) : null}
                  Yes, remove it!
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        {project.repo_url && (
          <DropdownMenuItem asChild>
            <a
              href={`https://${project.repo_url}`}
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:bg-gray-100 dark:hover:bg-gray-800 flex items-center"
            >
              <GitBranch className="w-4 h-4 mr-2" />
              Show GitHub
            </a>
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );

  const { statusComponent, description } = getProjectStatus();

  return (
    <div className={styles.card}>
      <div className="p-5 space-y-5">
        <div className="w-full flex flex-col items-start">
          <div className="w-full">
            <div className="flex items-center w-full space-x-2">
              <div className="flex items-center justify-between w-full">
                <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 line-clamp-1">
                  {project.name || "your frame..."}
                </div>
              </div>
              {statusComponent}
              {renderDropdownMenu()}
            </div>
            <div className="mt-1 space-y-1">
              <p className="text-xs text-gray-500">
                Created{" "}
                {new Date(project.created_at).toLocaleString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </p>
            </div>
          </div>
          {description && (
            <div className="w-full">
              <Label>{description}</Label>
            </div>
          )}
        </div>
        {project.frontend_url && project.latestBuild && (
          <div className="flex items-center gap-3">
            {project?.latestBuild?.status === "success" && (
              <Button
                variant="default"
                onClick={handleShare}
                disabled={isSubmitting}
              >
                <Share className="w-4 h-4 mr-2" />
                Share
              </Button>
            )}
            {/* {(
            <Button
              onClick={onHandleDeploy}
              className="flex-1 h-10"
              variant="default"
              disabled={isSubmitting}
            >
              <ArrowsUpFromLine className="w-4 h-4 mr-2" />
              Deploy
            </Button>
          )} */}
            <Link href={project.frontend_url} className="flex-1">
              <Button variant="outline" className="w-full h-10">
                <ExternalLink className="w-4 h-4 mr-2" />
                Open
              </Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

function ProjectDetailView({ projectId }: ProjectDetailViewProps) {
  const { context } = useFrameSDK();
  const userContext = context?.user;
  const [project, setProject] = useState<Project | null>(null);
  const [logs, setLogs] = useState<Log[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [updatePrompt, setUpdatePrompt] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchProject = useCallback(async () => {
    if (!projectId) return;
    try {
      const response = await fetch(`/api/projects?id=${projectId}`);
      if (!response.ok) throw new Error("Failed to fetch project");

      const data = await response.json();
      const fetchedProject: Project = data.projects?.[0];
      setProject(fetchedProject);
      if (fetchedProject) {
        const allLogs =
          fetchedProject.jobs?.flatMap((job) => job.logs || []) || [];
        const sortedLogs = allLogs.sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        );

        // Merge new logs with existing Vercel logs
        setLogs((prevLogs) => {
          // Keep existing Vercel logs
          const vercelLogs = prevLogs.filter((log) => log.source === "vercel");

          // Add new logs, avoiding duplicates by ID
          const existingIds = new Set(vercelLogs.map((log) => log.id));
          const newLogs = sortedLogs.filter((log) => !existingIds.has(log.id));

          // Combine and sort all logs
          return [...vercelLogs, ...newLogs].sort(
            (a, b) =>
              new Date(b.created_at).getTime() -
              new Date(a.created_at).getTime(),
          );
        });
      }
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      setError(err.message || "Failed to load project");
    }
  }, [projectId]);

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;

    if (projectId) {
      fetchProject(); // initial fetch
      interval = setInterval(() => {
        fetchProject();
      }, 2500);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [projectId, fetchProject]);

  const handleSubmitUpdate = async () => {
    if (!updatePrompt.trim()) return;
    setIsSubmitting(true);
    try {
      const response = await fetch("/api/update-code", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          projectId,
          prompt: updatePrompt,
          userContext,
        }),
      });
      if (!response.ok) {
        throw new Error("Failed to submit update");
      }
      setUpdatePrompt("");
      await fetchProject();
    } catch (err) {
      console.error("Error submitting update:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // const onHandleDeploy = async () => {
  //   if (!project) return;
  //   setIsSubmitting(true);

  //   try {
  //     const response = await fetch("/api/deploy-project", {
  //       method: "POST",
  //       headers: {
  //         "Content-Type": "application/json",
  //       },
  //       body: JSON.stringify({
  //         projectId: project.id,
  //         userContext: userContext,
  //       }),
  //     });
  //     if (!response.ok) throw new Error("Deployment failed");
  //     await fetchProject();
  //   } catch (err) {
  //     console.error("Deployment error:", err);
  //   } finally {
  //     setIsSubmitting(false);
  //   }
  // };

  const onHandleTryAutofix = async () => {
    if (!project) return;
    setIsSubmitting(true);

    // Filter logs to get only stderr entries
    const errorLogs = logs
      .filter((log) => log.data?.logs?.some((l) => l.type === "stderr"))
      .flatMap(
        (log) =>
          log.data?.logs &&
          log.data.logs.filter(
            (l) =>
              l.type === "stderr" &&
              l.payload?.text &&
              !l.payload.text.startsWith("warning"),
          ),
      )
      .map((log) => log?.payload?.text)
      .join("\n");

    const autofixPrompt = `Please fix the following build errors:\n\n${errorLogs}`;
    console.log("Autofix prompt:", autofixPrompt);
    try {
      const response = await fetch("/api/update-code", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          projectId,
          prompt: autofixPrompt,
          userContext,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to submit autofix update");
      }

      // Refresh project data after update
      await fetchProject();
    } catch (err) {
      console.error("Error submitting autofix:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!project && !error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-500 p-4 text-center break-words max-w-md">
        Error: {error}
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-gray-500 p-4 text-center">Project not found</div>
    );
  }

  const renderDebugView = () => {
    if (userContext?.fid.toString() != "13596") return;
    const { jobs, builds, latestJob, latestBuild, ...rest } = project;
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { logs, ...latestJobRest } = latestJob || {};
    return (
      <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg max-w-sm break-all space-4">
        Debug View
        <div className="bg-gray-200 dark:bg-gray-700 p-2 rounded-lg">
          {JSON.stringify(rest, null, 2)}
        </div>
        <div className="bg-gray-200 dark:bg-gray-700 p-2 rounded-lg">
          <h3 className="text-lg font-semibold m-2">Latest Job</h3>
          {latestJob ? (
            <p>{JSON.stringify(latestJobRest)}</p>
          ) : (
            <p>No job found</p>
          )}
        </div>
        <div className="bg-gray-200 dark:bg-gray-700 p-2 rounded-lg">
          <h3 className="text-lg font-semibold m-2">Latest Build</h3>
          {latestBuild ? (
            <p>{JSON.stringify(latestBuild)}</p>
          ) : (
            <p>No build found</p>
          )}
        </div>
        <div className="bg-gray-200 dark:bg-gray-700 p-2 rounded-lg">
          <h3 className="text-lg font-semibold m-2">Jobs</h3>
          {jobs?.map((job) => <p key={job.id}>{JSON.stringify(job)}</p>)}
        </div>
        <div className="bg-gray-200 dark:bg-gray-700 p-2 rounded-lg">
          <h3 className="text-lg font-semibold m-2">Builds</h3>
          {builds?.map((build) => (
            <p key={build.id}>{JSON.stringify(build)}</p>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="w-full mx-auto space-y-6 mb-6 px-4 max-w-[100vw-2rem] lg:max-w-4xl xl:max-w-5xl">
      <ProjectInfoCard
        project={project}
        // onHandleDeploy={onHandleDeploy}
        isSubmitting={isSubmitting}
      />

      <Tabs defaultValue="edit" className="w-full">
        <TabsList className="w-full bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
          <TabsTrigger
            value="edit"
            className="flex-1 data-[state=active]:bg-white dark:data-[state=active]:bg-gray-700 data-[state=active]:shadow-sm"
          >
            Edit
          </TabsTrigger>
          <TabsTrigger
            value="preview"
            className="flex-1 data-[state=active]:bg-white dark:data-[state=active]:bg-gray-700 data-[state=active]:shadow-sm"
          >
            Preview
          </TabsTrigger>
          <TabsTrigger
            value="conversation"
            className="flex-1 data-[state=active]:bg-white dark:data-[state=active]:bg-gray-700 data-[state=active]:shadow-sm"
          >
            Conversation
          </TabsTrigger>
          {userContext?.fid.toString() === "13596" && (
            <TabsTrigger
              value="debug"
              className="flex-1 data-[state=active]:bg-white dark:data-[state=active]:bg-gray-700 data-[state=active]:shadow-sm"
            >
              Debug
            </TabsTrigger>
          )}{" "}
        </TabsList>

        <TabsContent value="edit" className="space-y-4 mt-4">
          <UpdatePromptInput
            project={project}
            updatePrompt={updatePrompt}
            setUpdatePrompt={setUpdatePrompt}
            isSubmitting={isSubmitting}
            handleSubmitUpdate={handleSubmitUpdate}
            userContext={userContext}
            onHandleTryAutofix={onHandleTryAutofix}
          />
        </TabsContent>

        <TabsContent value="preview" className="space-y-4 mt-4">
          <FramePreviewCard project={project} />
        </TabsContent>

        <TabsContent value="conversation" className="space-y-4 mt-4">
          <ConversationCard project={project} />
        </TabsContent>
        <TabsContent value="debug" className="space-y-4 mt-4">
          {renderDebugView()}
        </TabsContent>
      </Tabs>

      <ActivityLogCard logs={logs} />
    </div>
  );
}

export default ProjectDetailView;
