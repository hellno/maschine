import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "./ui/card";
import { Button } from "./ui/button";
import { CheckCircle2, XCircle, Share, ExternalLink } from "lucide-react";
import sdk from "@farcaster/frame-sdk";
import { cn } from "~/lib/utils";

interface ProjectOverviewCardProps {
  projectId: string;
  name: string;
  repoUrl?: string;
  frontendUrl?: string;
  createdAt: string;
  onClick?: () => void;
  selected?: boolean;
}

export function ProjectOverviewCard({
  projectId,
  name,
  repoUrl,
  frontendUrl,
  createdAt,
  onClick,
  selected = false,
}: ProjectOverviewCardProps) {
  const handleShare = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (frontendUrl) {
      const shareText = `Check out my frame "${name}" built with frameception`;
      const shareUrl = `https://warpcast.com/~/compose?text=${encodeURIComponent(
        shareText
      )}&embeds[]=${encodeURIComponent(frontendUrl)}`;
      sdk.actions.openUrl(shareUrl);
    }
  };

  const handleOpenFrame = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (frontendUrl) {
      sdk.actions.openUrl(
        `https://warpcast.com/~/frames/launch?domain=${frontendUrl}`
      );
    }
  };

  return (
    <Card
      className={cn(
        "transition-colors cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50",
        selected && "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
      )}
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-base">{name || projectId}</CardTitle>
            <CardDescription className="text-xs">
              Created {new Date(createdAt).toLocaleDateString()}
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardFooter className="pt-2">
        <div className="gap-2 w-full grid grid-cols-2">
          {frontendUrl && (
            <>
              <Button
                size="sm"
                onClick={handleShare}
                className="flex-1"
              >
                <Share className="w-4 h-4 mr-2" />
                Share
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleOpenFrame}
                className="flex-1"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Open
              </Button>
            </>
          )}
        </div>
      </CardFooter>
    </Card>
  );
}
