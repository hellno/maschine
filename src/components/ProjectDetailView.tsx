import { useEffect, useState, useCallback, useMemo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "./ui/sheet";
import { GitBranch, Globe, ArrowUp, Share } from "lucide-react";
import { Button } from "./ui/button";
import { FrameContext } from "@farcaster/frame-core";
import sdk from "@farcaster/frame-sdk";
import { Job, Log, Project, VercelLogData } from "~/lib/types";

// Styles object
const styles = {
  chatBubble: {
    base: "w-fit max-w-[85%] sm:max-w-[75%] rounded-lg py-2 px-3 mb-2 break-words",
    user: "ml-auto bg-blue-500 text-white rounded-br-none",
    bot: "mr-auto bg-gray-100 text-gray-900 rounded-bl-none",
  },
  container: "space-y-6 max-w-3xl mx-auto",
  loadingSpinner:
    "animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900",
};

interface ProjectDetailViewProps {
  projectId: string | null;
  userContext?: FrameContext["user"];
}

// Project Info Card Component
function ProjectInfoCard({ project }: { project: Project }) {
  const handleShare = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click event
    if (project.frontend_url) {
      const shareText = `Check out my frame ${project.name} built with frameception`;
      const shareUrl = `https://warpcast.com/~/compose?text=${encodeURIComponent(
        shareText
      )}&embeds[]=${encodeURIComponent(project.frontend_url)}`;
      sdk.actions.openUrl(shareUrl);
    }
  };

  const hasAnyJobsPending = (project?.jobs || []).some(
    (job) => job.status === "pending"
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-top justify-between">
          {project.name || "Project Details"}
          {project.frontend_url && (
            <Button variant="secondary" size="sm" onClick={handleShare}>
              Share Frame
              <Share className="w-5 h-5 flex-shrink-0" />
            </Button>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4">
          <div className="flex items-center gap-2">
            <GitBranch className="w-5 h-5 flex-shrink-0" />
            <button
              onClick={() => sdk.actions.openUrl(project.repo_url)}
              className="text-blue-500 hover:text-blue-700 flex items-center gap-1 break-all"
            >
              GitHub Repository
            </button>
          </div>
          {hasAnyJobsPending && (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
          )}
          {project.frontend_url && (
            <div className="flex items-center gap-2">
              <Globe className="w-5 h-5 flex-shrink-0" />
              <button
                onClick={() =>
                  sdk.actions.openUrl(
                    `https://warpcast.com/~/frames/launch?domain=${project.frontend_url!}`
                  )
                }
                className="text-blue-500 hover:text-blue-700 flex items-center gap-1 break-all"
              >
                Open Frame
              </button>
            </div>
          )}
          <div className="text-sm text-gray-500">
            Created on {new Date(project.created_at).toLocaleDateString()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Conversation History Card Component
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
          {jobs?.map((job) => (
            <div key={job.id} className="space-y-2">
              <div
                className={`${styles.chatBubble.base} ${styles.chatBubble.user}`}
              >
                {job.data.prompt}
              </div>
              <div
                className={`${styles.chatBubble.base} ${styles.chatBubble.bot}`}
              >
                {job.data.result || job.data.error || "✅"}
              </div>
            </div>
          ))}
          {(!jobs || jobs.length === 0) && (
            <div className="text-center text-gray-500">
              No conversations yet
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
          <textarea
            rows={4}
            value={updatePrompt}
            onChange={(e) => setUpdatePrompt(e.target.value)}
            placeholder="Describe the changes you'd like to make to your frame..."
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
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function LogViewer({ logs }: { logs: VercelLogData[] }) {
  const [showAllLogs, setShowAllLogs] = useState(false);

  // Filter and process logs
  const processedLogs = useMemo(() => {
    if (!logs) return [];
    return logs
      .filter((log) => showAllLogs || log.type === "stderr")
      .filter((log) => log.payload?.text?.trim()) // Remove empty logs
      .map((log) => ({
        ...log,
        timestamp: new Date(log.payload.date).toUTCString(),
        isError: log.type === "stderr",
      }));
  }, [logs, showAllLogs]);

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

// Activity Log Card Component
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
    return colors[source as keyof typeof colors] || colors.unknown;
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

  const fetchProject = useCallback(async () => {
    try {
      if (!projectId) return;

      const response = await fetch(`/api/projects?id=${projectId}`);
      if (!response.ok) throw new Error("Failed to fetch project");
      const data = await response.json();
      const project = data.projects?.[0];
      setProject(project);
      console.log("project", project);
      // Set logs from each job's logs
      if (project) {
        const allLogs = project.jobs.flatMap((job: Job) => job.logs || []);
        // Sort logs by creation date, newest first
        const sortedLogs = allLogs.sort(
          (a: Log, b: Log) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setLogs(sortedLogs);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load project");
    }
  }, [projectId]);

  const fetchProject = useCallback(async () => {
    try {
      if (!projectId) return;

      const response = await fetch(`/api/projects?id=${projectId}`);
      if (!response.ok) throw new Error("Failed to fetch project");
      const data = await response.json();
      const project = data.projects?.[0];
      setProject(project);
      console.log("project", project);
      
      // Set logs from each job's logs
      if (project) {
        const allLogs = project.jobs.flatMap((job: Job) => job.logs || []);
        // Sort logs by creation date, newest first
        const sortedLogs = allLogs.sort(
          (a: Log, b: Log) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setLogs(sortedLogs);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load project");
    }
  }, [projectId]);

  const pollJobStatus = useCallback(async (jobId: string) => {
    try {
      const response = await fetch(`/api/job/${jobId}`);
      if (!response.ok) throw new Error("Failed to fetch job status");
      const data = await response.json();
      console.log("Job ", jobId, "status:", data);
      
      // Refetch project data to get latest changes
      await fetchProject();
      
      // Update logs with any new entries
      setLogs((prevLogs) => {
        const newLogs: Log[] = data.logs || [];
        const existingLogIds = new Set(prevLogs.map((log) => log.id));
        const uniqueNewLogs = newLogs.filter(
          (log) => !existingLogIds.has(log.id)
        );
        return [...uniqueNewLogs, ...prevLogs];
      });

      // Continue polling if job is still pending
      if (data.status === "pending") {
        setTimeout(() => pollJobStatus(jobId), 2000);
      }
    } catch (err) {
      console.error("Error polling job status:", err);
    }
  }, [fetchProject]);

  const pollVercelStatus = useCallback(async () => {
    console.log(
      "Polling Vercel status...",
      project?.id,
      project?.vercel_project_id
    );
    if (!project?.vercel_project_id) return;

    try {
      const response = await fetch(`/api/vercel-status/${project.id}`);
      if (!response.ok) throw new Error("Failed to fetch Vercel status");

      const data = await response.json();
      setDeploymentStatus(data.status);
      console.log("Vercel deployment data:", data);
      // Continue polling if build is in progress
      if (data.status === "BUILDING" || data.status === "INITIALIZING") {
        setTimeout(() => pollVercelStatus(), 5000);
      }

      // Add deployment status to logs if changed
      if (data.status !== deploymentStatus) {
        setLogs((prev) => [
          {
            id: crypto.randomUUID(),
            created_at: new Date().toISOString(),
            source: "vercel",
            text: `Deployment status: ${data.status}`,
            data: data,
          },
          ...prev,
        ]);
      }
    } catch (err) {
      console.error("Error polling Vercel status:", err);
    }
  }, [project?.id, project?.vercel_project_id, deploymentStatus]);

  useEffect(() => {
    fetchProject();
  }, [fetchProject]);

  useEffect(() => {
    if (project?.vercel_project_id) {
      pollVercelStatus();
    }
  }, [project?.vercel_project_id, pollVercelStatus]);

  useEffect(() => {
    if (project?.jobs) {
      const pendingJobs = project.jobs.filter(
        (job) => job.status === "pending"
      );
      pendingJobs.forEach((job) => pollJobStatus(job.id));
    }
  }, [project?.jobs, pollJobStatus]);

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
          projectId: projectId,
          prompt: updatePrompt,
          userContext,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to submit update");
      }

      const data = await response.json();
      // Start polling the new job
      if (data.jobId) {
        pollJobStatus(data.jobId);
      }

      // Clear the input after successful submission
      setUpdatePrompt("");
      // Refresh project data to show new job
      fetchProject();
    } catch (error) {
      console.error("Error submitting update:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!project) {
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
      <ProjectInfoCard project={project} />
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
