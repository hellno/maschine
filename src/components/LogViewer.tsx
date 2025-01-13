interface Log {
  text: string;
}

interface LogViewerProps {
  logs: Log[];
  isLoading?: boolean;
}

export function LogViewer({ logs, isLoading = false }: LogViewerProps) {
  return (
    <div className="relative w-full h-56 bg-gray-50 rounded-lg p-4">
      {isLoading ? (
        <div className="text-center text-gray-600">Loading logs...</div>
      ) : (
        <div className="h-full overflow-y-auto">
          <pre className="text-sm text-gray-600 whitespace-pre-wrap">
            {logs.length ? [...logs].reverse().map((l) => l.text).join("\n") : "Waiting for logs..."}
          </pre>
        </div>
      )}
      <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-gray-50 to-transparent pointer-events-none" />
    </div>
  );
}
