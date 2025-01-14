/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState, useCallback } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { ExternalLink, GitBranch, Globe, ArrowUp } from "lucide-react";
import { Button } from "./ui/button";
import { FrameContext } from "@farcaster/frame-core";

interface Log {
  id: string;
  created_at: string;
  source: string;
  text: string;
}

interface Job {
  id: string;
  status: "pending" | "completed" | "failed";
  created_at: string;
  data: any;
}

interface Project {
  id: string;
  created_at: string;
  repo_url: string;
  frontend_url: string;
  fid_owner: number;
  jobs?: Job[];
  logs?: Log[];
}

interface ProjectDetailViewProps {
  projectId: string;
  userContext?: FrameContext["user"];
}

export function ProjectDetailView({
  projectId,
  userContext,
}: ProjectDetailViewProps) {
  const chatBubbleStyles = {
    base: "w-fit rounded-lg py-2 px-3 mb-2",
    user: "ml-auto bg-blue-500 text-white rounded-br-none",
    bot: "mr-auto bg-gray-100 text-gray-900 rounded-bl-none",
  };

  const [project, setProject] = useState<Project | null>(null);
  const [logs, setLogs] = useState<Log[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [updatePrompt, setUpdatePrompt] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchProject = useCallback(async () => {
    try {
      const response = await fetch(`/api/projects?id=${projectId}`);
      if (!response.ok) throw new Error("Failed to fetch project");
      const data = await response.json();
      setProject(data.projects?.[0]);
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
      // Update logs with any new entries
      setLogs((prevLogs) => {
        const newLogs = data.logs || [];
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
  }, []);

  useEffect(() => {
    fetchProject();
  }, [fetchProject]);

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
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Project Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4">
            <div className="flex items-center gap-2">
              <GitBranch className="w-5 h-5" />
              <a
                href={project.repo_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:text-blue-700 flex items-center gap-1"
              >
                GitHub Repository
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
            {project.frontend_url && (
              <div className="flex items-center gap-2">
                <Globe className="w-5 h-5" />
                <a
                  href={project.frontend_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-500 hover:text-blue-700 flex items-center gap-1"
                >
                  Live Demo
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            )}
            <div className="text-sm text-gray-500">
              Created on {new Date(project.created_at).toLocaleDateString()}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Conversation History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {project.jobs?.map((job) => (
              <div key={job.id} className="space-y-2">
                {/* User message */}
                <div
                  className={`${chatBubbleStyles.base} ${chatBubbleStyles.user}`}
                >
                  {job.data.prompt}
                </div>

                {/* Bot response */}
                <div
                  className={`${chatBubbleStyles.base} ${chatBubbleStyles.bot}`}
                >
                  {job.data.result || job.data.error || "✅"}
                </div>
              </div>
            ))}
            {(!project.jobs || project.jobs.length === 0) && (
              <div className="text-center text-gray-500">
                No conversations yet
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Update Frame</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <textarea
              rows={4}
              value={updatePrompt}
              onChange={(e) => setUpdatePrompt(e.target.value)}
              placeholder="Describe the changes you'd like to make to your frame..."
              className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isSubmitting}
            />
            <Button
              onClick={handleSubmitUpdate}
              disabled={!updatePrompt.trim() || isSubmitting || !userContext}
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
                    <div className="flex items-start justify-between">
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
                    <div className="mt-1 text-sm text-gray-700 whitespace-pre-wrap">
                      {log.text}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
