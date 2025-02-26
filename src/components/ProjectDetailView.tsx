"use client";

import { useEffect, useState, useCallback } from "react";
import {
  GitBranch,
  Share,
  ExternalLink,
  Copy,
  ArrowsUpFromLine,
} from "lucide-react";
import { Button } from "./ui/button";
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
  onHandleDeploy,
  isSubmitting,
}: {
  project: Project;
  onHandleDeploy: () => void;
  isSubmitting: boolean;
}) {
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

  // Find the latest update timestamp from jobs
  const getLastUpdateTime = () => {
    const jobs = project.jobs || [];
    if (jobs.length === 0) return null;

    const sortedJobs = [...jobs].sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );

    return new Date(sortedJobs[0].created_at);
  };

  const lastUpdateTime = getLastUpdateTime();

  return (
    <div className={styles.card}>
      <div className="p-5 space-y-5">
        <div className="flex items-start">
          <div className="w-full">
            <div className="flex items-center justify-between w-full">
              <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 line-clamp-1">
                {project.name}
              </div>
              {project?.latestBuild?.status && (
                <div className="px-4 py-2 text-md font-medium rounded-full bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                  Live
                </div>
              )}
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
              {lastUpdateTime && (
                <p className="text-xs text-gray-500">
                  Last updated{" "}
                  {lastUpdateTime.toLocaleString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {project?.latestBuild?.status === "success" ? (
            <Button
              variant="default"
              onClick={handleShare}
              disabled={isSubmitting}
            >
              <Share className="w-4 h-4 mr-2" />
              Share
            </Button>
          ) : (
            <Button
              onClick={onHandleDeploy}
              className="flex-1 h-10"
              variant="default"
              disabled={isSubmitting}
            >
              <ArrowsUpFromLine className="w-4 h-4 mr-2" />
              Deploy
            </Button>
          )}
          {project.frontend_url && (
            <Link href={project.frontend_url} className="flex-1">
              <Button variant="outline" className="w-full h-10">
                <ExternalLink className="w-4 h-4 mr-2" />
                Open Frame
              </Button>
            </Link>
          )}

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="icon" className="h-10 w-10">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-4 h-4"
                >
                  <circle cx="12" cy="12" r="1" />
                  <circle cx="12" cy="5" r="1" />
                  <circle cx="12" cy="19" r="1" />
                </svg>
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
              <DropdownMenuSeparator />
              {project.repo_url && (
                <DropdownMenuItem asChild>
                  <Link
                    href={`https://${project.repo_url}`}
                    className="transition-colors hover:bg-gray-100 dark:hover:bg-gray-800 flex items-center"
                  >
                    <GitBranch className="w-4 h-4 mr-2" />
                    Show GitHub
                  </Link>
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
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

  const onHandleDeploy = async () => {
    if (!project) return;
    setIsSubmitting(true);

    try {
      const response = await fetch("/api/deploy-project", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          projectId: project.id,
          userContext: userContext,
        }),
      });
      if (!response.ok) throw new Error("Deployment failed");
      await fetchProject();
    } catch (err) {
      console.error("Deployment error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const onHandleTryAutofix = async () => {
    if (!project) return;
    setIsSubmitting(true);

    console.log("logs", logs);
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

  return (
    <div className="w-full mx-auto space-y-6 mb-6 px-4 max-w-[100vw-2rem] lg:max-w-4xl xl:max-w-5xl">
      <ProjectInfoCard
        project={project}
        onHandleDeploy={onHandleDeploy}
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
        </TabsList>

        <TabsContent value="edit" className="space-y-4 mt-4">
          <UpdatePromptInput
            project={project}
            logs={logs}
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
      </Tabs>

      <ActivityLogCard logs={logs} />
    </div>
  );
}

export default ProjectDetailView;
