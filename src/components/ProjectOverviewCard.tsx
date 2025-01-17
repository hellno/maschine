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
          <div className="flex gap-2 items-center">
            <div className="flex flex-col items-center">
              {repoUrl ? (
                <CheckCircle2 className="w-4 h-4 text-green-500" />
              ) : (
                <XCircle className="w-4 h-4 text-red-500" />
              )}
              <span className="text-xs">Repo</span>
            </div>
            <div className="flex flex-col items-center">
              {frontendUrl ? (
                <CheckCircle2 className="w-4 h-4 text-green-500" />
              ) : (
                <XCircle className="w-4 h-4 text-red-500" />
              )}
              <span className="text-xs">Frontend</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardFooter className="pt-2">
        <div className="flex gap-2 w-full">
          {repoUrl && (
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                sdk.actions.openUrl(repoUrl);
              }}
              className="flex-1"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              GitHub
            </Button>
          )}
          {frontendUrl && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={handleOpenFrame}
                className="flex-1"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Open Frame
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleShare}
                className="flex-1"
              >
                <Share className="w-4 h-4 mr-2" />
                Share
              </Button>
            </>
          )}
        </div>
      </CardFooter>
    </Card>
  );
}
