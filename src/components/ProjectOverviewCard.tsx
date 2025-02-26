import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardFooter,
} from "./ui/card";
import { Button } from "./ui/button";
import { Share, ExternalLink, Hammer } from "lucide-react";
import sdk from "@farcaster/frame-sdk";
import { cn } from "~/lib/utils";
import { Project } from "~/lib/types";
import Link from "next/link";

interface ProjectOverviewCardProps {
  project: Project;
  selected?: boolean;
}

export function ProjectOverviewCard({
  project,
  selected = false,
}: ProjectOverviewCardProps) {
  const name =
    project?.name ||
    project?.repo_url?.split("frameception-v2/")[1] ||
    project.id?.split("-")[0];

  const createdAt = project.created_at;
  const frontendUrl = project.frontend_url;

  const handleShare = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (frontendUrl) {
      const shareText = `Check out my frame "${name}" built with @maschine`;
      const shareUrl = `https://warpcast.com/~/compose?text=${encodeURIComponent(
        shareText,
      )}&embeds[]=${encodeURIComponent(frontendUrl)}`;
      sdk.actions.openUrl(shareUrl);
    }
  };

  return (
    <Card
      className={cn(
        "transition-colors cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50",
        selected && "border-blue-500 bg-blue-50 dark:bg-blue-900/20",
      )}
    >
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-base">{name || project.id}</CardTitle>
            <CardDescription className="text-xs">
              Created {new Date(createdAt).toLocaleDateString()}
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardFooter className="pt-2">
        <div className="gap-2 w-full grid grid-cols-2">
          <Link href={`/projects/${project.id}`} className="w-full flex-1">
            <Button variant="secondary" size="sm" className="w-full">
              <Hammer className="w-4 h-4 mr-2" />
              Edit
            </Button>
          </Link>
          {project.status === "deployed" && (
            <Button size="sm" onClick={handleShare} className="flex-1">
              <Share className="w-4 h-4 mr-2" />
              Share
            </Button>
          )}
          {frontendUrl && (
            <Link href={frontendUrl} className="flex-1 w-full">
              <Button variant="outline" size="sm" className="flex-1 w-full">
                <ExternalLink className="w-4 h-4 mr-2" />
                Open Frame
              </Button>
            </Link>
          )}
        </div>
      </CardFooter>
    </Card>
  );
}
