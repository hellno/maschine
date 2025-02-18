"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "~/components/ui/tabs";
import { Card, CardContent } from "~/components/ui/card";
import sdk, { FrameNotificationDetails } from "@farcaster/frame-sdk";

import { ArrowUp, AlertCircle, PlayCircle, Loader2 } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "~/components/ui/sheet";
import { FrameContext, Project } from "~/lib/types";
import { useCallback, useState } from "react";
import { ProjectDetailView } from "~/components/ProjectDetailView";
import { Button } from "~/components/ui/button";
import { useFrameSDK } from "~/hooks/useFrameSDK";
import { useProjects } from "~/hooks/useProjects";

const promptTemplates = [
  {
    title: "Link Tree",
    template:
      "Create a link tree frame that shows my social links and allows users to navigate between them. Include links to: Farcaster, GitHub, and other links I've shared recently.",
  },
  {
    title: "Image Gallery",
    template:
      "Create a frame that shows a gallery of images with next/previous navigation. Include 5 images or videos that I have shared recently.",
  },
  {
    title: "Quiz Game",
    template:
      "Make a multiple choice quiz game frame based on my recent casts. Include 2 questions with 4 options each and show the score at the end.",
  },
  {
    title: "Event Countdown",
    template:
      "Show a countdown timer for my event coming up at 5pm on Friday UTC.",
  },
];

const Page = () => {
  const { context } = useFrameSDK();
  const { createProject } = useProjects();
  const [inputValue, setInputValue] = useState("");
  const [flowState, setFlowState] = useState<
    "enteringPrompt" | "pending" | "success"
  >("enteringPrompt");
  const [creationError, setCreationError] = useState<string | null>(null);

  const [newProjectId, setNewProjectId] = useState<string | null>(null);

  const handleCreateProject = useCallback(async () => {
    try {
      if (inputValue.trim().length < 25) {
        throw new Error("Please enter at least 25 characters");
      }
      if (!context?.user?.fid) {
        throw new Error("User session not found");
      }

      setFlowState("pending");
      setCreationError(null);

      const response = await createProject.mutateAsync({
        prompt: inputValue,
        userContext: context.user,
      });

      const projectId = response.project_id;
      setNewProjectId(projectId);
      //   setSelectedProjectId(projectId);
      setFlowState("success");

      requestAnimationFrame(() => {
        const detailView = document.getElementById("project-detail-view");
        if (detailView) {
          detailView.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
    } catch (error) {
      console.error("Error creating project:", error);
      setCreationError(
        error instanceof Error ? error.message : "An unknown error occurred"
      );
      setFlowState("enteringPrompt");
    }
  }, [inputValue, context?.user, createProject]);

  return (
    <div className="space-y-6">
      <Card className="border-0 shadow-lg">
        <CardContent className="pt-6">
          <div className="space-y-6">
            <div className="relative">
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Describe your frame
                </label>
                <span className="text-sm text-gray-500">
                  {inputValue.length}/25
                </span>
              </div>
              <textarea
                rows={5}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Create a quiz game about crypto trends with 5 multiple choice questions"
                className="w-full p-4 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100"
              />
              <p className="text-sm text-gray-500 mt-2 text-left">
                Describe your frame in at least 25 characters. The more detail
                you provide, the better the frame will be. You can keep chatting
                with the AI later to improve your frame.
              </p>
            </div>

            {creationError && (
              <div className="text-red-500 font-bold mt-2 text-center">
                Error: {creationError}
              </div>
            )}

            <Button
              size="lg"
              className="w-full py-4 text-lg font-semibold"
              onClick={handleCreateProject}
              disabled={
                inputValue.trim().length < 25 ||
                flowState === "pending" ||
                createProject.isPending
              }
            >
              {flowState === "pending" || createProject.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {createProject.isPending
                    ? "Creating Project..."
                    : "Creating Project..."}
                </>
              ) : (
                "Start Building →"
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="mt-8">
        <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-4 uppercase tracking-wide">
          Popular Starting Points
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {promptTemplates.map((template) => (
            <button
              key={template.title}
              onClick={() => setInputValue(template.template)}
              className="group p-4 text-left rounded-xl border hover:border-blue-500 dark:border-gray-700 dark:hover:border-blue-600 transition-all bg-white dark:bg-gray-800 hover:shadow-sm"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900 dark:text-gray-100">
                  {template.title}
                </span>
                <ArrowUp className="w-4 h-4 text-gray-400 group-hover:text-blue-500 transition-colors transform rotate-45" />
              </div>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                {template.template}
              </p>
            </button>
          ))}
        </div>
      </div>

      {creationError && (
        <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-xl text-red-600 dark:text-red-400 flex items-center">
          <AlertCircle className="w-5 h-5 mr-2" />
          {creationError}
        </div>
      )}

      {(flowState === "pending" || flowState === "success") && newProjectId && (
        <div
          id="project-detail-view"
          className="flex flex-col items-center gap-4 w-full max-w-3xl mx-auto px-4 scroll-target"
        >
          <ProjectDetailView
            projectId={newProjectId}
            userContext={context?.user}
          />
        </div>
      )}
    </div>
  );
};

export default Page;
