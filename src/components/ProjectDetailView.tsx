import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { ProjectStatusIndicator } from "./ProjectStatusIndicator";
import { getProjectStatus } from "~/lib/types/project-status";
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
import { cn } from "~/lib/utils";

// Styles object
const styles = {
  container: "max-w-4xl mx-auto space-y-6 p-6",
  card: "bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700",
  cardHeader: "px-6 py-4 border-b border-gray-100 dark:border-gray-700",
  cardContent: "p-6",
  deploymentStatus: {
    ready: "text-green-600 bg-green-50 dark:bg-green-900/20",
    error: "text-red-600 bg-red-50 dark:bg-red-900/20",
    building: "text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20",
    pending: "text-blue-600 bg-blue-50 dark:bg-blue-900/20",
  },
  badge: "px-2.5 py-0.5 rounded-full text-xs font-medium inline-flex items-center gap-1",
  link: "text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 inline-flex items-center gap-2 transition-colors",
  chat: {
    userMessage: "bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg",
    botMessage: "bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg", 
    timestamp: "text-xs text-gray-500 mt-1",
    container: "space-y-4"
  }
};

interface ProjectDetailViewProps {
  projectId: string | null;
  userContext?: FrameContext["user"];
}

// Refs for polling control
interface PollingRefs {
  pollTimeout: React.MutableRefObject<NodeJS.Timeout | undefined>;
  isPollingActive: React.MutableRefObject<boolean>;
}

// Project Info Card Component
function ProjectInfoCard({ project }: { project: Project }) {
  const status = getProjectStatus(project);
  
  return (
    <div className={styles.card}>
      <div className="p-6 space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
              {project.name}
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Created {new Date(project.created_at).toLocaleDateString()}
            </p>
          </div>
          {project.frontend_url && (
            <Button variant="outline" size="sm" onClick={() => 
              sdk.actions.openUrl(`https://warpcast.com/~/frames/launch?domain=${project.frontend_url}`)
            }>
              <Globe className="w-4 h-4 mr-2" />
              Open Frame
            </Button>
          )}
        </div>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:gap-6">
          <div className="flex items-center gap-2">
            <div className={cn(
              styles.badge,
              status.state === 'ready' && styles.deploymentStatus.ready,
              status.state === 'error' && styles.deploymentStatus.error,
              status.state === 'building' && styles.deploymentStatus.building,
              status.state === 'setting_up' && styles.deploymentStatus.pending,
            )}>
              {status.state === 'building' && <div className="w-2 h-2 rounded-full bg-yellow-600 animate-pulse" />}
              {status.message}
            </div>
          </div>
          
          <a href={project.repo_url} 
             target="_blank" 
             rel="noopener noreferrer" 
             className={styles.link}>
            <GitBranch className="w-4 h-4" />
            View Repository
          </a>
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
                  {job.status === 'pending' ? (
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
              No conversations yet. Start by describing the changes you'd like to make.
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

  const pollTimeoutRef = useRef<NodeJS.Timeout>();
  const isPollingActiveRef = useRef(true);

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

  const pollJobStatus = useCallback(
    async (jobId: string) => {
      try {
        // Don't continue if polling was cancelled
        if (!isPollingActiveRef.current) return;

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

        // Continue polling if job is still pending and polling is active
        if (data.status === "pending" && isPollingActiveRef.current) {
          pollTimeoutRef.current = setTimeout(() => pollJobStatus(jobId), 2000);
        }
      } catch (err) {
        console.error("Error polling job status:", err);
      }
    },
    [fetchProject]
  );

  const pollVercelStatus = useCallback(async () => {
    if (!project?.vercel_project_id || !isPollingActiveRef.current) return;

    try {
      const response = await fetch(`/api/vercel-status/${project.id}`);
      if (!response.ok) throw new Error("Failed to fetch Vercel status");

      const data = await response.json();
      setDeploymentStatus(data.status);
      console.log("Vercel deployment data:", data);

      // Continue polling if build is in progress and polling is active
      if (
        (data.status === "BUILDING" || data.status === "INITIALIZING") &&
        isPollingActiveRef.current
      ) {
        pollTimeoutRef.current = setTimeout(() => pollVercelStatus(), 5000);
      }

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

  // Add cleanup effect
  useEffect(() => {
    // Set polling as active when component mounts
    isPollingActiveRef.current = true;

    // Cleanup function to run when component unmounts
    return () => {
      // Stop all polling
      isPollingActiveRef.current = false;

      // Clear any pending timeouts
      if (pollTimeoutRef.current) {
        clearTimeout(pollTimeoutRef.current);
      }

      console.log("Cleaned up polling for project", projectId);
    };
  }, [projectId]);

  useEffect(() => {
    fetchProject();
  }, [fetchProject]);

  useEffect(() => {
    if (project?.vercel_project_id && isPollingActiveRef.current) {
      pollVercelStatus();
    }
  }, [project?.vercel_project_id, pollVercelStatus]);

  useEffect(() => {
    if (project?.jobs && isPollingActiveRef.current) {
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
