import { CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { ProjectStatus } from "~/lib/types/project-status";
import { Label } from "./ui/label";

export function ProjectStatusIndicator({ status }: { status: ProjectStatus }) {
  const statusStyles = {
    created: {
      bg: "bg-blue-100",
      text: "text-blue-700",
      icon: null,
    },
    deploying: {
      bg: "bg-yellow-100",
      text: "text-yellow-700",
      icon: (
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-700" />
      ),
    },
    deployed: {
      bg: "bg-green-100",
      text: "text-green-700",
      icon: <CheckCircle className="w-4 h-4" />,
    },
    failed: {
      bg: "bg-red-100",
      text: "text-red-700",
      icon: <XCircle className="w-4 h-4" />,
    },
    error: {
      bg: "bg-red-100",
      text: "text-red-700",
      icon: <AlertCircle className="w-4 h-4" />,
    },
    unknown: {
      bg: "bg-gray-100",
      text: "text-gray-700",
      icon: (
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-700" />
      ),
    },
  };

  const style = statusStyles[status.state];

  return (
    <Label
      className={`h-10 px-4 inline-flex items-center justify-center gap-2 rounded-md ${style.bg}`}
    >
      <div className={`flex items-center ${style.text}`}>
        {style.icon ? style.icon : null}
        {status.message && (
          <span className="ml-2 font-medium">{status.message}</span>
        )}
      </div>
    </Label>
  );
}
