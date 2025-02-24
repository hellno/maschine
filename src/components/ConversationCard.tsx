"use client";

import { ConversationMessage } from "./ConversationMessage";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { Project } from "~/lib/types";

function ConversationCard({ project }: { project: Project }) {
  const jobs =
    project.jobs
      ?.filter(
        (job) => job.type === "update_code" || job.type === "setup_project",
      )
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      ) || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Conversation</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4 max-w-full">
          {jobs.length > 0 ? (
            jobs.map((job) => (
              <div key={job.id} className="space-y-2">
                <ConversationMessage
                  text={job.data.prompt}
                  timestamp={new Date(job.created_at).toLocaleString()}
                  type="user"
                />
                <ConversationMessage
                  text={
                    job.status === "pending"
                      ? "Processing..."
                      : job.data.error
                        ? job.data.error
                        : job.data.result || ""
                  }
                  timestamp={new Date(job.created_at).toLocaleString()}
                  type="bot"
                  isError={!!job.data.error}
                />
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
