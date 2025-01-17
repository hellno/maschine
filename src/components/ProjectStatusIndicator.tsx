import { CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { ProjectStatus } from "~/lib/types/project-status";

export function ProjectStatusIndicator({ status }: { status: ProjectStatus }) {
  // AI! add status 'unknown' which should render a spinner and a skeleton 
  const statusStyles = {
    setting_up: {
      bg: 'bg-blue-100',
      text: 'text-blue-700',
      icon: <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-700" />,
    },
    building: {
      bg: 'bg-yellow-100',
      text: 'text-yellow-700',
      icon: <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-700" />,
    },
    ready: {
      bg: 'bg-green-100',
      text: 'text-green-700',
      icon: <CheckCircle className="w-4 h-4" />,
    },
    failed: {
      bg: 'bg-red-100',
      text: 'text-red-700',
      icon: <XCircle className="w-4 h-4" />,
    },
    error: {
      bg: 'bg-red-100',
      text: 'text-red-700',
      icon: <AlertCircle className="w-4 h-4" />,
    },
  };

  const style = statusStyles[status.state];

  return (
    <div className={`flex items-center gap-2 rounded-md ${style.bg}`}>
      <div className={`flex items-center ${style.text}`}>
        {style.icon}
        <span className="ml-2 font-medium">{status.message}</span>
      </div>
      {status.error && (
        <div className="mt-1 text-sm text-red-600">
          Error: {status.error}
        </div>
      )}
    </div>
  );
}
