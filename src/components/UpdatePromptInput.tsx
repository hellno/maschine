"use client";

import { Button } from "./ui/button";
import { Info, LoaderCircle } from "lucide-react";
import { Project, UserContext } from "~/lib/types";
import { useEffect, useRef, useState } from "react";

interface UpdatePromptInputProps {
  project: Project;
  updatePrompt: string;
  setUpdatePrompt: (prompt: string) => void;
  isSubmitting: boolean;
  handleSubmitUpdate: () => void;
  userContext?: UserContext;
  onHandleTryAutofix: () => void;
}

function UpdatePromptInput({
  project,
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

  const { hasAnyJobsPending, latestJob, latestBuild } = project;

  const hasBuildErrors =
    latestJob?.status === "failed" || latestBuild?.status === "error";

  return (
    <div className="space-y-4 max-w-full">
      {isSubmitting || hasAnyJobsPending ? (
        <div className="p-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50 rounded-lg text-sm text-amber-800 dark:text-amber-300">
          <div className="flex items-center gap-4">
            <LoaderCircle className="w-4 h-4 animate-spin  border-amber-500 dark:border-amber-400" />
            <span>
              Maschine is working on your project. We will notify you when
              it&apos;s done. Thanks for building with Maschine!
            </span>
          </div>
        </div>
      ) : hasBuildErrors ? (
        <div className="flex flex-col gap-4 p-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50 rounded-lg text-sm text-amber-800 dark:text-amber-300">
          <span>
            Maschine has made an error in the last change. You can try to fix it
            manually or let Maschine try to autofix it (beta).
          </span>
          <Button
            onClick={onHandleTryAutofix}
            disabled={hasAnyJobsPending}
            className="w-full"
          >
            Try Autofix
          </Button>
        </div>
      ) : null}
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
              disabled={hasAnyJobsPending || isSubmitting}
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
              !userContext ||
              hasAnyJobsPending ||
              isSubmitting
            }
            className="w-full flex items-center justify-center gap-2 py-5 text-base transition-all focus:ring-4 focus:ring-slate-300"
            size="lg"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Building...</span>
              </>
            ) : (
              <>
                <span>Update Frame</span>
              </>
            )}
          </Button>
        </>
      )}
    </div>
  );
}

export default UpdatePromptInput;
