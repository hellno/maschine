import { useState, useEffect, useCallback } from "react";
import { Button } from "./ui/button";
import { Check, Loader2 } from "lucide-react";
import sdk from "@farcaster/frame-sdk";

interface PinFrameButtonProps {
  projectId: string;
  className?: string;
}

export function PinFrameButton({ projectId, className }: PinFrameButtonProps) {
  const [isPinning, setIsPinning] = useState(false);
  const [isFramePinned, setIsFramePinned] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isContextLoaded, setIsContextLoaded] = useState(false); // New state

  // Initialize SDK context and event listeners
  useEffect(() => {
    const loadContext = async () => {
      const frameContext = await sdk.context;
      if (!frameContext) {
        setIsContextLoaded(true);
        return;
      }

      setIsFramePinned(frameContext.client.added);
      setIsContextLoaded(true); // Mark context as loaded
    };

    loadContext();

    const handleFrameAdded = () => setIsFramePinned(true);
    const handleFrameRemoved = () => setIsFramePinned(false);

    sdk.on("frameAdded", handleFrameAdded);
    sdk.on("frameRemoved", handleFrameRemoved);

    return () => {
      sdk.off("frameAdded", handleFrameAdded);
      sdk.off("frameRemoved", handleFrameRemoved);
    };
  }, []);

  const handlePinFrame = useCallback(async () => {
    setIsPinning(true);
    setError(null);

    try {
      const result = await sdk.actions.addFrame();

      if (result.added) {
        // Only call API if frame was successfully pinned
        const response = await fetch("/api/increment-frame-pins", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ projectId }),
        });

        if (!response.ok) {
          throw new Error("Failed to increment pin count");
        }
      } else {
        setError(result.reason || "Failed to pin frame");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsPinning(false);
    }
  }, [projectId]);

  return (
    <div className="flex flex-col items-center gap-2">
      <Button
        onClick={handlePinFrame}
        disabled={!isContextLoaded || isPinning || isFramePinned}
        className={className}
      >
        {!isContextLoaded ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Loading...
          </>
        ) : isPinning ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Pinning...
          </>
        ) : isFramePinned ? (
          <>
            <Check className="mr-2 h-4 w-4" />
            Pinned!
          </>
        ) : (
          "Pin Frame"
        )}
      </Button>
      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}
