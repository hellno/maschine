import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { FrameContext, Project } from "~/lib/types";
import { useRouter } from "next/navigation";

export function useProjects(fid?: number) {
  const queryClient = useQueryClient();
  const router = useRouter();

  const query = useQuery<{ projects: Project[] }>({
    queryKey: ["projects", fid],
    queryFn: async () => {
      if (!fid) return { projects: [] };
      
      const response = await fetch(`/api/projects?fid=${fid}`);
      if (!response.ok) throw new Error("Failed to fetch projects");
      return response.json();
    },
    enabled: !!fid,
  });

  const createProjectMutation = useMutation({
    mutationFn: async (payload: { prompt: string; userContext: FrameContext["user"] }) => {
      const response = await fetch("/api/new-frame-project", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error("Failed to create project");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", fid] });
      router.push("/projects/all");
    },
  });

  const removeProjectMutation = useMutation({
    mutationFn: async (projectId: string) => {
      const response = await fetch("/api/projects", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: projectId }),
      });
      if (!response.ok) throw new Error("Failed to remove project");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", fid] });
    },
  });

  return {
    projects: query?.data?.projects || [],
    isLoading: query.isLoading,
    refetch: query.refetch,
    error: query.error,
    createProject: createProjectMutation,
    removeProject: removeProjectMutation,
  };
}
