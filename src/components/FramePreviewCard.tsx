import { Card, CardContent } from "./ui/card";
import { Project } from "~/lib/types";
import {
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Monitor,
  LoaderCircle,
  CircleX,
} from "lucide-react";
import { Button } from "./ui/button";
import { useState } from "react";

interface FramePreviewCardProps {
  project: Project;
}

const FramePreviewCard = ({ project }: FramePreviewCardProps) => {
  const [refreshKey, setRefreshKey] = useState(0);
  const hasAnySuccessfulBuild = project?.builds?.some(
    (build) => build.status === "success",
  );
  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
  };

  const renderPendingBuildInfo = () => {
    let text = "";
    let icon;

    if (project.latestBuild?.status === "error") {
      text = "Last change failed! Go to edit and try autofix or fix manually";
      icon = <CircleX className="h-4 w-4 text-red-500" />;
    } else if (
      project.latestBuild?.status === "queued" ||
      project.latestBuild?.status === "building"
    ) {
      icon = <LoaderCircle className="h-4 w-4 animate-spin text-amber-500" />;
      text = hasAnySuccessfulBuild
        ? "New version building..."
        : "Initial build in progress...";
    } else {
      return null;
    }

    return (
      <div className="p-4 border border-amber-200 bg-amber-50 dark:border-amber-800/50 dark:bg-amber-900/20 rounded-lg text-sm">
        <div className="flex items-center gap-3">
          {icon}
          <div className="space-y-1">
            <p className="font-medium">{text}</p>
            {hasAnySuccessfulBuild && (
              <p className="opacity-80">
                Preview shows previous successful build
              </p>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <>
      {renderPendingBuildInfo()}

      <Card className="overflow-hidden border">
        <div className="flex w-full items-center text-[14px] font-medium text-gray-500 h-10 border-alpha-200 border-b bg-muted gap-1 px-2">
          <div className="relative mx-1 flex-1">
            <div className="flex h-6 w-full min-w-0 items-center rounded-full border border-transparent bg-gray-200 px-2.5 text-gray-900">
              {project.frontend_url ? (
                <span className="truncate text-xs">{project.frontend_url}</span>
              ) : (
                <span className="text-xs text-gray-500">No URL available</span>
              )}
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 rounded-md text-gray-500"
            disabled
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 rounded-md text-gray-500"
            disabled
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 rounded-md text-gray-500"
            onClick={handleRefresh}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        <CardContent className="p-0">
          <div className="w-full">
            {project.frontend_url && hasAnySuccessfulBuild ? (
              <div className="w-full aspect-square relative overflow-hidden">
                <iframe
                  key={refreshKey}
                  src={project.frontend_url}
                  className="w-full h-full border-0"
                  sandbox="allow-scripts allow-same-origin allow-forms"
                  loading="lazy"
                  title="Frame Preview"
                />
              </div>
            ) : (
              <div className="w-full aspect-square bg-gray-100 flex flex-col items-center justify-center">
                <Monitor className="h-12 w-12 text-gray-300 mb-4" />
                <p className="text-gray-500 font-medium">
                  No preview available, yet
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
      <p className="text-sm text-gray-400 mt-1">
        Transactions and some actions like showing user profiles and tokens are
        not supported in this preview. They will work in the actual Frame.
      </p>
    </>
  );
};

export default FramePreviewCard;
