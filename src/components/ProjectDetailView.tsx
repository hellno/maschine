import { useEffect, useState, useCallback } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { ProjectStatusIndicator } from "./ProjectStatusIndicator";
import {
  getProjectStatus,
  ProjectStatus,
  VercelBuildStatus,
} from "~/lib/types/project-status";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "./ui/sheet";
import { GitBranch, ArrowUp, Share, ExternalLink, Copy } from "lucide-react";
import { Button } from "./ui/button";
import { FrameContext } from "@farcaster/frame-core";
import sdk from "@farcaster/frame-sdk";
import { Job, Log, Project, VercelLogData } from "~/lib/types";

const styles = {
  container: "max-w-4xl mx-auto space-y-6 py-2",
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
    userMessage: "bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg",
    botMessage: "bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg",
    timestamp: "text-xs text-gray-500 mt-1",
    container: "space-y-4",
  },
};

interface ProjectDetailViewProps {
  projectId: string | null;
  userContext?: FrameContext["user"];
}

function ProjectInfoCard({
  project,
  status,
}: {
  project: Project;
  status: ProjectStatus;
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
        shareText
      )}&embeds[]=${encodeURIComponent(project.frontend_url)}`;
      sdk.actions.openUrl(shareUrl);
    }
  };

  return (
    <div className={styles.card}>
      <div className="p-6 space-y-6">
        <div className="flex flex-row sm:items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
              {project.name}
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Created {new Date(project.created_at).toLocaleDateString()}
            </p>
          </div>
          <ProjectStatusIndicator status={status} />
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          {project.frontend_url && (
            <>
              <Button
                variant="outline"
                onClick={() =>
                  sdk.actions.openUrl(
                    `https://warpcast.com/~/frames/launch?domain=${project.frontend_url}`
                  )
                }
                className="flex-1"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Open Frame
              </Button>
              <Button
                variant="outline"
                onClick={handleShare}
                className="flex-1"
              >
                <Share className="w-4 h-4 mr-2" />
                Share on Warpcast
              </Button>
              <Button
                variant="outline"
                onClick={handleCopyUrl}
                className="flex-1"
              >
                <Copy className="w-4 h-4 mr-2" />
                Copy URL
              </Button>
            </>
          )}
          {project.repo_url && (
            <Button
              variant="outline"
              onClick={() => sdk.actions.openUrl(project.repo_url!)}
              className="flex-1"
            >
              <GitBranch className="w-4 h-4 mr-2" />
              View Repository
            </Button>
          )}
        </div>
        {status.error && (
          <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg text-red-600 dark:text-red-400 text-sm">
            {status.error}
          </div>
        )}
      </div>
    </div>
  );
}

function ConversationCard({
  project,
  updatePrompt,
  setUpdatePrompt,
  isSubmitting,
  handleSubmitUpdate,
  userContext,
}: {
  project: Project;
  updatePrompt: string;
  setUpdatePrompt: (prompt: string) => void;
  isSubmitting: boolean;
  handleSubmitUpdate: () => void;
  userContext?: FrameContext["user"];
}) {
  const jobs =
    project.jobs?.filter(
      (job) => job.type === "update_code" || job.type === "setup_project"
    ) || [];

  const hasAnyJobsPending = jobs.some((job) => job.status === "pending");

  return (
    <Card>
      <CardHeader>
        <CardTitle>Conversation</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {jobs.length > 0 ? (
            jobs.map((job) => (
              <div key={job.id} className="space-y-2">
                <div className={styles.chat.userMessage}>
                  <p className="text-sm text-gray-900 dark:text-gray-100">
                    {job.data.prompt}
                  </p>
                  <p className={styles.chat.timestamp}>
                    {new Date(job.created_at).toLocaleString()}
                  </p>
                </div>
                <div className={styles.chat.botMessage}>
                  {job.status === "pending" ? (
                    <div className="flex items-center gap-2 text-gray-500">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
                      Processing...
                    </div>
                  ) : job.data.error ? (
                    <p className="text-red-600">{job.data.error}</p>
                  ) : (
                    <p className="text-gray-700 dark:text-gray-300">
                      {job.data.result || "✅"}
                    </p>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="text-center text-gray-500 py-8">
              No conversations yet. Start by describing the changes you&apos;d
              like to make.
            </div>
          )}
        </div>
        <div className="mt-12 space-y-4">
          {hasAnyJobsPending && (
            <div className="p-4 bg-gray-50 rounded-lg text-sm text-gray-500">
              There are pending jobs for this project. Please wait for them to
              finish.
            </div>
          )}
          {!hasAnyJobsPending && (
            <>
            <textarea
            rows={4}
            value={updatePrompt}
            onChange={(e) => setUpdatePrompt(e.target.value)}
            placeholder="Describe the changes you'd like to make..."
            className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isSubmitting || hasAnyJobsPending}
          />
          <Button
            onClick={handleSubmitUpdate}
            disabled={
              !updatePrompt.trim() ||
              isSubmitting ||
              !userContext ||
              hasAnyJobsPending
            }
            className="w-full flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Updating...
              </>
            ) : (
              <>
                Update Frame
                <ArrowUp className="w-4 h-4" />
              </>
            )}
          </Button></>
        )}
        </div>
      </CardContent>
    </Card>
  );
}

function LogViewer({ logs }: { logs: VercelLogData[] }) {
  const [showAllLogs, setShowAllLogs] = useState(false);

  const processedLogs = logs
    ? logs
        .filter((log) => showAllLogs || log.type === "stderr")
        .filter((log) => log.payload?.text?.trim())
        .map((log) => ({
          ...log,
          timestamp: new Date(log.payload.date).toUTCString(),
          isError: log.type === "stderr",
        }))
    : [];

  return (
    <div className="flex flex-col h-full">
      <div className="flex-none p-4 border-b">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Build Logs</h3>
          <label className="flex items-center space-x-2 text-sm">
            <input
              type="checkbox"
              checked={showAllLogs}
              onChange={(e) => setShowAllLogs(e.target.checked)}
              className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
            />
            <span>Show all logs</span>
          </label>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto">
        <div className="divide-y divide-gray-100">
          {processedLogs.map((log, index) => (
            <div
              key={log.payload.id || index}
              className={`p-3 ${
                log.isError ? "bg-red-50" : "hover:bg-gray-50"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-medium px-2 py-0.5 rounded ${
                        log.isError
                          ? "bg-red-100 text-red-700"
                          : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {log.type}
                    </span>
                    <span className="text-xs text-gray-500">
                      {log.timestamp}
                    </span>
                  </div>
                  <div
                    className={`mt-1 text-sm font-mono whitespace-pre-wrap break-words ${
                      log.isError ? "text-red-700" : "text-gray-700"
                    }`}
                  >
                    {log.payload.text}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ActivityLogCard({ logs }: { logs: Log[] }) {
  const getSourceColor = (source: string) => {
    const colors = {
      frontend: "text-blue-600",
      backend: "text-green-600",
      vercel: "text-purple-600",
      github: "text-gray-600",
      farcaster: "text-pink-600",
      unknown: "text-gray-400",
    };
    return (colors as any)[source] || colors.unknown;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Activity Log</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="max-h-96 overflow-y-auto border rounded-lg">
          {logs.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              No activity logs yet
            </div>
          ) : (
            <div className="divide-y">
              {logs.map((log) => (
                <div key={log.id} className="p-3 hover:bg-gray-50">
                  <div className="flex items-start justify-between flex-wrap gap-2">
                    <div
                      className={`text-sm font-medium ${getSourceColor(
                        log.source
                      )}`}
                    >
                      {log.source}
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(log.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div className="mt-1 text-sm text-gray-700 whitespace-pre-wrap break-words">
                    {log.text}
                    {log.data && log.data.logs && (
                      <Sheet>
                        <SheetTrigger asChild>
                          <button className="ml-2 px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-md transition-colors">
                            View Details
                          </button>
                        </SheetTrigger>
                        <SheetContent className="w-[400px] sm:w-[540px] lg:w-[680px] overflow-y-auto flex flex-col h-full">
                          <div className="flex-none">
                            <SheetHeader>
                              <SheetTitle>Log Details</SheetTitle>
                              <SheetDescription>
                                {new Date(log.created_at).toLocaleString()}
                              </SheetDescription>
                            </SheetHeader>
                          </div>
                          <LogViewer logs={log.data.logs} />
                        </SheetContent>
                      </Sheet>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function ProjectDetailView({
  projectId,
  userContext,
}: ProjectDetailViewProps) {
  const [project, setProject] = useState<Project | null>(null);
  const [logs, setLogs] = useState<Log[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [updatePrompt, setUpdatePrompt] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deploymentStatus, setDeploymentStatus] = useState<string | null>(null);
  const [vercelBuildStatus, setVercelBuildStatus] =
    useState<VercelBuildStatus | null>(null);

  const projectStatus = getProjectStatus(project, vercelBuildStatus);

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
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setLogs(sortedLogs);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load project");
    }
  }, [projectId]);

  const fetchVercelStatus = useCallback(async () => {
    if (!project?.vercel_project_id) return;
    try {
      const response = await fetch(`/api/vercel-status/${project.id}`);
      if (!response.ok) throw new Error("Failed to fetch Vercel status");
      const data = await response.json();
      setDeploymentStatus(data.status);
      setVercelBuildStatus(data.status);

      // If status changed, add log entry
      if (data.status !== deploymentStatus) {
        setLogs((prev) => [
          {
            id: crypto.randomUUID(),
            created_at: new Date().toISOString(),
            source: "vercel",
            text: `Deployment status: ${data.status}`,
            data,
          },
          ...prev,
        ]);
      }
    } catch (err) {
      console.error("Error fetching Vercel status:", err);
    }
  }, [project?.vercel_project_id, project?.id, deploymentStatus]);

  // Consolidated polling approach
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;

    if (projectId) {
      fetchProject(); // initial fetch
      interval = setInterval(() => {
        fetchProject();
        fetchVercelStatus();
      }, 5000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [projectId, fetchProject, fetchVercelStatus]);

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

  if (!project && !error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  if (error) {
    return <div className="text-red-500 p-4 text-center">Error: {error}</div>;
  }

  if (!project) {
    return (
      <div className="text-gray-500 p-4 text-center">Project not found</div>
    );
  }

  return (
    <div className={styles.container}>
      <ProjectInfoCard project={project} status={projectStatus} />
      <ConversationCard
        project={project}
        updatePrompt={updatePrompt}
        setUpdatePrompt={setUpdatePrompt}
        isSubmitting={isSubmitting}
        handleSubmitUpdate={handleSubmitUpdate}
        userContext={userContext}
      />
      <ActivityLogCard logs={logs} />
    </div>
  );
}
