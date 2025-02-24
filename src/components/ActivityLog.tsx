"use client";

import LogViewer from "./LogViewer";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "./ui/sheet";
import { Log } from "~/lib/types";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "~/components/ui/collapsible";
import { Maximize2, Minimize2 } from "lucide-react";
import { useState } from "react";
import { Button } from "./ui/button";

function ActivityLogCard({ logs }: { logs: Log[] }) {
  const [isOpen, setIsOpen] = useState(false);

  const getSourceColor = (source: string) => {
    const colors: Record<string, string> = {
      frontend: "text-blue-600",
      backend: "text-green-600",
      vercel: "text-purple-600",
      github: "text-gray-600",
      farcaster: "text-pink-600",
      unknown: "text-gray-400",
    };
    return colors[source] || colors.unknown;
  };

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card>
        <CardHeader>
          <CardTitle>
            <CollapsibleTrigger className="flex items-center justify-between min-w-full">
              Activity Log
              <Button variant="outline" size="sm" className="">
                {isOpen ? (
                  <>
                    <Minimize2 className="h-4 w-4" />
                    <p className="text-sm font-medium">Close</p>
                  </>
                ) : (
                  <>
                    <Maximize2 className="h-4 w-4" />
                    <p className="text-sm font-medium">Open</p>
                  </>
                )}
              </Button>
            </CollapsibleTrigger>
          </CardTitle>
        </CardHeader>
        <CollapsibleContent>
          <CardContent>
            <div className="max-h-96 overflow-y-auto border rounded-lg">
              {logs.length === 0 ? (
                <div className="p-4 text-center text-gray-500">
                  No activity logs yet
                </div>
              ) : (
                <div className="divide-y">
                  {logs.map((log) => (
                    <div key={log.id} className="p-3 hover:bg-gray-50">
                      <div className="flex items-start justify-between flex-wrap gap-2">
                        <div
                          className={`text-sm font-medium ${getSourceColor(
                            log.source,
                          )}`}
                        >
                          {log.source}
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(log.created_at).toLocaleString()}
                        </div>
                      </div>
                      <div className="mt-1 text-sm text-gray-700 whitespace-pre-wrap break-words">
                        {log.text}
                        {log.data && log.data.logs && (
                          <Sheet>
                            <SheetTrigger asChild>
                              <button className="ml-2 px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-md transition-colors">
                                View Details
                              </button>
                            </SheetTrigger>
                            <SheetContent className="w-[400px] sm:w-[540px] lg:w-[680px] overflow-y-auto flex flex-col h-full">
                              <div className="flex-none">
                                <SheetHeader>
                                  <SheetTitle>Log Details</SheetTitle>
                                  <SheetDescription>
                                    {new Date(log.created_at).toLocaleString()}
                                  </SheetDescription>
                                </SheetHeader>
                              </div>
                              <LogViewer logs={log.data.logs} />
                            </SheetContent>
                          </Sheet>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

export default ActivityLogCard;
