import { Card, CardHeader, CardTitle, CardDescription, CardFooter } from "./ui/card";
import { CheckCircle2, XCircle } from "lucide-react";

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
  return (
    <Card
      className={`transition-colors cursor-pointer ${
        selected
          ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
          : "hover:border-gray-400"
      }`}
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-base">{name}</CardTitle>
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
        <div className="flex gap-3 text-sm">
          {repoUrl && (
            <a
              href={repoUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-700 hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              GitHub
            </a>
          )}
          {frontendUrl && (
            <a
              href={frontendUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-700 hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              Live Demo
            </a>
          )}
        </div>
      </CardFooter>
    </Card>
  );
}
