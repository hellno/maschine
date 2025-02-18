import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { Project } from "~/lib/types";

export function useProjects(fid?: number) {
  const queryClient = useQueryClient();

  const query = useQuery<Project[]>({
    queryKey: ["projects", fid],
    queryFn: async () => {
      const response = await fetch(`/api/projects?fid=${fid}`);
      if (!response.ok) throw new Error("Failed to fetch projects");
      return response.json();
    },
    enabled: !!fid,
  });

  const createProjectMutation = useMutation({
    mutationFn: async (payload: { prompt: string; userContext: any }) => {
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
    },
  });

  return {
    projects: query.data || [],
    isLoading: query.isLoading,
    error: query.error,
    createProject: createProjectMutation,
  };
}
