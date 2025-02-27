"use client";

import { Card, CardContent } from "~/components/ui/card";

import { AlertCircle, Loader2, ListPlus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "~/components/ui/button";
import { useFrameSDK } from "~/hooks/useFrameSDK";
import { useProjects } from "~/hooks/useProjects";
import { useRouter } from "next/navigation";

const promptTemplates = [
  {
    title: "Link Tree",
    template:
      "Create a link tree frame that shows my social links and allows users to navigate between them. Include links to: Farcaster, GitHub, and other links I've shared recently.",
  },
  {
    title: "Image Gallery",
    template:
      "Create a frame that shows a gallery of images with next and previous navigation. Include 5 images or videos that I have shared recently on Farcaster.",
  },
  {
    title: "Quiz Game",
    template:
      "Make a multiple choice quiz game frame based on my recent casts. Include 2 questions with 4 options each and show the score at the end.",
  },
  {
    title: "Event Countdown",
    template:
      "Show a countdown timer for my event coming up at 5pm on Friday UTC. Make it look MySpace-y and 90s style. Include a countdown timer with a retro design.",
  },
];

const MIN_WORD_COUNT = 25;

const Page = () => {
  const router = useRouter();
  const { context } = useFrameSDK();
  const { createProject } = useProjects(context?.user.fid);
  const [inputValue, setInputValue] = useState("");
  const [flowState, setFlowState] = useState<
    "enteringPrompt" | "pending" | "success"
  >("enteringPrompt");
  const [creationError, setCreationError] = useState<string | null>(null);
  const [newProjectId, setNewProjectId] = useState<string | null>(null);
  const wordCount = inputValue ? inputValue.trim().split(" ").length : 0;

  const handleCreateProject = useCallback(async () => {
    try {
      if (wordCount < MIN_WORD_COUNT) {
        throw new Error(`Please enter at least ${MIN_WORD_COUNT} characters`);
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
        error instanceof Error ? error.message : "An unknown error occurred",
      );
      setFlowState("enteringPrompt");
    }
  }, [inputValue, context?.user, createProject]);

  useEffect(() => {
    if ((flowState === "pending" || flowState === "success") && newProjectId) {
      router.push(`/projects/${newProjectId}`);
    }
  }, [flowState, newProjectId, router]);

  return (
    <div className="space-y-6">
      <Card className="border-0 shadow-lg">
        <CardContent className="pt-6">
          <div className="space-y-6">
            <div className="relative space-y-4">
              <div className="flex justify-between items-center mb-2">
                <label className="block text-xl font-medium text-gray-700 dark:text-gray-300">
                  What can I help you build?
                </label>
              </div>
              <textarea
                rows={5}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Create a quiz game about crypto trends with 5 multiple choice questions"
                className="w-full p-4 border rounded-xl dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100"
              />

              <Button
                size="lg"
                className="w-full py-4 text-xl font-semibold"
                onClick={handleCreateProject}
                disabled={
                  wordCount < MIN_WORD_COUNT ||
                  flowState === "pending" ||
                  createProject.isPending
                }
              >
                {flowState === "pending" || createProject.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Building...
                  </>
                ) : (
                  "Build"
                )}
              </Button>
              {wordCount < MIN_WORD_COUNT && (
                <div className="flex flex-col space-y-2">
                  <span className="text-sm text-gray-500 text-left"></span>
                  <p className="text-sm text-gray-500 text-left">
                    {MIN_WORD_COUNT - wordCount} more{" "}
                    {MIN_WORD_COUNT - wordCount > 1 ? "words" : "word 🤩"}.
                    Describe your frame in at least {MIN_WORD_COUNT} words. The
                    more detail you provide, the better Maschine will build it.
                    You can chat with Maschine to keep changing your frame.
                  </p>
                </div>
              )}
            </div>

            {creationError && (
              <div className="text-red-500 font-bold mt-2 text-center">
                Error: {creationError}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card className="mt-4 border-0 shadow-lg">
        <CardContent className="pt-6">
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
                  <ListPlus className="w-5 h-5 text-gray-400" />
                </div>
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                  {template.template}
                </p>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
      {creationError && (
        <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-xl text-red-600 dark:text-red-400 flex items-center">
          <AlertCircle className="w-5 h-5 mr-2" />
          {creationError}
        </div>
      )}
    </div>
  );
};

export default Page;
