"use client";

import { Loader2, PlusCircle, RefreshCcw } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ProjectOverviewCard } from "~/components/ProjectOverviewCard";
import { Button } from "~/components/ui/button";
import { useFrameSDK } from "~/hooks/useFrameSDK";
import { useProjects } from "~/hooks/useProjects";

const Page = () => {
  const router = useRouter();
  const { context } = useFrameSDK();
  const { projects, isLoading, refetch } = useProjects(context?.user.fid);

  const onCreateProject = () => {
    router.push("/projects/new");
  };
  return (
    <div className="grid grid-cols-1 gap-4">
      {isLoading ? (
        <div className="text-center text-gray-500 py-8">
          <Loader2 className="mr-2 h-4 w-4 animate-spin inline" />
          Loading projects...
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center">
          <div className="text-center text-gray-500 py-6">No projects yet.</div>
          <div className="flex justify-center gap-4">
            <Button onClick={() => onCreateProject()}>
              <PlusCircle className="h-6 w-6 mr-1" />
              New
            </Button>
            <Button variant="secondary" onClick={() => refetch()}>
              <RefreshCcw className="h-6 w-6 mr-1" />
              Refresh
            </Button>
          </div>
        </div>
      ) : (
        projects.map((project) => (
          <Link key={project.id} href={`/projects/${project.id}`}>
            <ProjectOverviewCard key={project.id} project={project} />
          </Link>
        ))
      )}
    </div>
  );
};

export default Page;
