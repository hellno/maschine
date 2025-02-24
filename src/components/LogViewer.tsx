import { useState } from "react";
import { VercelLogData } from "~/lib/types";

function LogViewer({ logs }: { logs: VercelLogData[] }) {
  const [showAllLogs, setShowAllLogs] = useState(false);

  const processedLogs = logs
    ? logs
        .filter(
          (log) =>
            showAllLogs ||
            (log.type === "stderr" && !log.payload?.text.startsWith("warning")),
        )
        .filter((log) => log.payload?.text?.trim())
        .map((log) => ({
          ...log,
          timestamp: new Date(log.payload.date).toUTCString(),
          isError: log.type === "stderr",
        }))
    : [];

  return (
    <div className="flex flex-col h-full">
      <div className="flex-none p-4 border-b">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Build Logs</h3>
          <label className="flex items-center space-x-2 text-sm">
            <input
              type="checkbox"
              checked={showAllLogs}
              onChange={(e) => setShowAllLogs(e.target.checked)}
              className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
            />
            <span>Show all logs</span>
          </label>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto">
        <div className="divide-y divide-gray-100">
          {processedLogs.map((log, index) => (
            <div
              key={log.payload.id || index}
              className={`p-3 ${
                log.isError ? "bg-red-50" : "hover:bg-gray-50"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-medium px-2 py-0.5 rounded ${
                        log.isError
                          ? "bg-red-100 text-red-700"
                          : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {log.type}
                    </span>
                    <span className="text-xs text-gray-500">
                      {log.timestamp}
                    </span>
                  </div>
                  <div
                    className={`mt-1 text-sm font-mono whitespace-pre-wrap break-words ${
                      log.isError ? "text-red-700" : "text-gray-700"
                    }`}
                  >
                    {log.payload.text}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default LogViewer;
