import { useState, useMemo } from "react";
import { Button } from "./ui/button";

interface ConversationMessageProps {
  text: string;
  timestamp: string;
  type: "user" | "bot";
  isError?: boolean;
}

export function ConversationMessage({
  text,
  timestamp,
  type,
  isError,
}: ConversationMessageProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const { displayText, hasMore } = useMemo(() => {
    const lines = text.split("\n").filter((line) => line.trim());
    const shouldCollapse = lines.length > 3;
    const displayText =
      shouldCollapse && !isExpanded ? lines.slice(0, 3).join("\n") : text;

    return {
      displayText,
      hasMore: shouldCollapse && !isExpanded,
    };
  }, [text, isExpanded]);

  if (!text) return;

  return (
    <div
      className={`${
        type === "user"
          ? "bg-blue-50 dark:bg-blue-900/20"
          : "bg-gray-50 dark:bg-gray-800/50"
      } p-4 rounded-lg overflow-hidden`}
    >
      <div
        className={`${
          isError
            ? "text-red-600"
            : type === "user"
            ? "text-gray-900 dark:text-gray-100"
            : "text-gray-700 dark:text-gray-300"
        } break-words overflow-wrap-anywhere whitespace-pre-wrap`}
      >
        {displayText}
      </div>

      {hasMore && (
        <Button
          size="sm"
          variant="ghost"
          className="mt-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          onClick={() => setIsExpanded(true)}
        >
          Read more...
        </Button>
      )}
      {isExpanded && (
        <Button
          size="sm"
          variant="ghost"
          className="mt-2 text-sm"
          onClick={() => setIsExpanded(false)}
        >
          Show less
        </Button>
      )}

      <p className="text-xs text-gray-500 mt-1">{timestamp}</p>
    </div>
  );
}
