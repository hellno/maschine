"use client";

import { ConversationMessage } from "./ConversationMessage";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
} from "./ui/card";
import { Project } from "~/lib/types";
import { useEffect, useState, useRef } from "react";
import { CheckCircle, XCircle, Clock, Loader } from "lucide-react";

// Define a type for our conversation items
type ConversationItem = {
  id: string;
  created_at: string;
  type: "user" | "system";
  content: string;
  status?: "building" | "queued" | "success" | "error";
  isError?: boolean;
};

function ConversationCard({ project }: { project: Project }) {
  const [conversationItems, setConversationItems] = useState<
    ConversationItem[]
  >([]);

  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Combine jobs and builds into conversation items
  useEffect(() => {
    // Filter relevant jobs
    const relevantJobs =
      project.jobs?.filter(
        (job) => job.type === "update_code" || job.type === "setup_project",
      ) || [];

    // Map jobs to conversation items (user messages)
    const jobItems: ConversationItem[] = relevantJobs.map((job) => ({
      id: `job-${job.id}`,
      created_at: job.created_at,
      type: "user",
      content: job.data.prompt,
      isError: false,
    }));

    // Map builds to conversation items (system responses)
    const buildItems: ConversationItem[] =
      project.builds?.map((build) => ({
        id: `build-${build.id}`,
        created_at: build.created_at,
        type: "system",
        content:
          build.data?.meta?.githubCommitMessage ||
          "Maschine is working on it...",
        status: build.status as "building" | "queued" | "success" | "error",
        isError: build.status === "error",
      })) || [];

    const combined = [...jobItems, ...buildItems].sort(
      (a, b) =>
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    );

    setConversationItems(combined);
  }, [project]);

  // Keep track of previous message count to determine if we should auto-scroll
  const prevItemCountRef = useRef(0);
  
  // Scroll to bottom only when new messages are added
  useEffect(() => {
    if (chatContainerRef.current && conversationItems.length > prevItemCountRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
    prevItemCountRef.current = conversationItems.length;
  }, [conversationItems]);

  // Get status icon based on build status
  const getStatusIcon = (status?: string) => {
    switch (status) {
      case "success":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "error":
        return <XCircle className="w-4 h-4 text-red-500" />;
      case "building":
        return <Loader className="w-4 h-4 text-blue-500 animate-spin" />;
      case "queued":
        return <Clock className="w-4 h-4 text-yellow-500" />;
      default:
        return null;
    }
  };

  return (
    <Card className="flex flex-col">
      <CardHeader className="flex-none border-b-slate-300">
        <CardTitle>Conversation</CardTitle>
        <CardDescription>Scroll up to see previous messages</CardDescription>
      </CardHeader>
      <CardContent className="flex-grow p-0 overflow-hidden">
        <div
          ref={chatContainerRef}
          className="h-[420px] overflow-y-auto p-4 space-y-4 max-w-full"
        >
          {conversationItems.length > 0 ? (
            conversationItems.map((item) => (
              <div key={item.id} className="flex items-start">
                {item.type === "system" && (
                  <div className="mr-2 mt-1">{getStatusIcon(item.status)}</div>
                )}
                <div
                  className={`flex-grow ${item.type === "user" ? "ml-auto max-w-[80%]" : "mr-auto max-w-[80%]"}`}
                >
                  <ConversationMessage
                    text={item.content}
                    timestamp={new Date(item.created_at).toLocaleString()}
                    type={item.type === "user" ? "user" : "bot"}
                    isError={item.isError}
                  />
                </div>
              </div>
            ))
          ) : (
            <div className="text-center text-gray-500 py-8">
              No conversations yet. Start by describing the changes you&apos;d
              like to make.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default ConversationCard;
