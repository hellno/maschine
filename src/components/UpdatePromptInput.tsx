"use client";

import { Button } from "./ui/button";
import { ArrowUp, Info } from "lucide-react";
import { Log, Project, UserContext } from "~/lib/types";
import { useEffect, useRef, useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "./ui/sheet";
import LogViewer from "./LogViewer";

interface UpdatePromptInputProps {
  project: Project;
  logs: Log[];
  updatePrompt: string;
  setUpdatePrompt: (prompt: string) => void;
  isSubmitting: boolean;
  handleSubmitUpdate: () => void;
  userContext?: UserContext;
  onHandleTryAutofix: () => void;
}

function UpdatePromptInput({
  project,
  logs,
  updatePrompt,
  setUpdatePrompt,
  isSubmitting,
  handleSubmitUpdate,
  userContext,
  onHandleTryAutofix,
}: UpdatePromptInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [charCount, setCharCount] = useState(0);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.max(80, textarea.scrollHeight)}px`;
    }
    setCharCount(updatePrompt.length);
  }, [updatePrompt]);

  const { latestJob, latestBuild } = project;
  const hasAnyJobsPending =
    isSubmitting ||
    latestJob?.status === "pending" ||
    latestJob?.status === "running" ||
    latestBuild?.status === "submitted" ||
    latestBuild?.status === "building" ||
    latestBuild?.status === "queued";

  const hasBuildErrors =
    latestJob?.status === "failed" || latestBuild?.status === "error";

  const buildErrorLog = logs
    .filter((log) => log.source === "vercel" && log.data)
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    )[0];

  return (
    <div className="space-y-4 max-w-full">
      {hasAnyJobsPending && (
        <div className="p-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50 rounded-lg text-sm text-amber-800 dark:text-amber-300">
          <div className="flex items-center gap-4">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-amber-500 dark:border-amber-400"></div>
            <span>
              Maschine is working on your project.
              <br /> Please wait for it to finish.
            </span>
          </div>
        </div>
      )}
      {!hasAnyJobsPending && (
        <>
          <div className="relative">
            <textarea
              ref={textareaRef}
              rows={4}
              value={updatePrompt}
              onChange={(e) => setUpdatePrompt(e.target.value)}
              placeholder="Describe your changes in detail. For example: 'Add a button that changes color when clicked' or 'Create a form with name and email fields'..."
              className="w-full p-4 bg-background text-foreground border-2 border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-slate-500 break-words overflow-wrap-anywhere shadow-sm placeholder:text-muted-foreground"
              disabled={isSubmitting || hasAnyJobsPending}
            />
            <div className="flex justify-between items-center mt-2 text-xs text-muted-foreground">
              <div className="flex items-center">
                <Info className="w-3 h-3 mr-1" />
                <span>Be specific about what you want to change</span>
              </div>
              <div
                className={`${charCount > 500 ? "text-amber-600 font-medium" : ""}`}
              >
                {charCount} characters
              </div>
            </div>
          </div>
          <Button
            onClick={handleSubmitUpdate}
            disabled={
              !updatePrompt.trim() ||
              isSubmitting ||
              !userContext ||
              hasAnyJobsPending
            }
            className="w-full flex items-center justify-center gap-2 py-5 text-base transition-all focus:ring-4 focus:ring-slate-300"
            size="lg"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Processing your update...</span>
              </>
            ) : (
              <>
                <span>Update Frame</span>
                <ArrowUp className="w-5 h-5" />
              </>
            )}
          </Button>
        </>
      )}
      {hasBuildErrors && (
        <div className="grid grid-cols-2 gap-4">
          <Button
            onClick={onHandleTryAutofix}
            disabled={isSubmitting || hasAnyJobsPending}
            className="w-full"
          >
            Try Autofix
          </Button>
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="outline" className="w-full">
                View Build Errors
              </Button>
            </SheetTrigger>
            <SheetContent className="w-[400px] sm:w-[540px] lg:w-[680px] overflow-y-auto flex flex-col h-full">
              <div className="flex-none">
                <SheetHeader>
                  <SheetTitle>Build Error Details</SheetTitle>
                  <SheetDescription>
                    {buildErrorLog &&
                      new Date(buildErrorLog.created_at).toLocaleString()}
                  </SheetDescription>
                </SheetHeader>
              </div>
              {buildErrorLog?.data?.logs && (
                <LogViewer logs={buildErrorLog.data.logs} />
              )}
            </SheetContent>
          </Sheet>
        </div>
      )}
    </div>
  );
}

export default UpdatePromptInput;
