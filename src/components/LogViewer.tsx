interface Log {
  text: string;
}

interface LogViewerProps {
  logs: Log[];
  isLoading?: boolean;
}

export function LogViewer({ logs, isLoading = false }: LogViewerProps) {
  return (
    <div className="w-full max-h-48 overflow-y-auto bg-gray-50 rounded-lg p-4">
      {isLoading ? (
        <div className="text-center text-gray-600">Loading logs...</div>
      ) : (
        <pre className="text-sm text-gray-600 whitespace-pre-wrap">
          {logs.length ? [...logs].reverse().map((l) => l.text).join("\n") : "Waiting for logs..."}
        </pre>
      )}
    </div>
  );
}
