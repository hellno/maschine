import { useState } from 'react';
import { Button } from './ui/button';
import { Check, Loader2 } from 'lucide-react';
import sdk from '@farcaster/frame-sdk';

interface PinFrameButtonProps {
  projectId: string;
  className?: string;
}

export function PinFrameButton({ projectId, className }: PinFrameButtonProps) {
  const [isPinning, setIsPinning] = useState(false);
  const [isPinned, setIsPinned] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePinFrame = async () => {
    setIsPinning(true);
    setError(null);

    try {
      // First try to pin the frame
      const result = await sdk.actions.addFrame();
      
      if (result.added) {
        // If frame was pinned successfully, increment the counter
        const response = await fetch('/api/increment-frame-pins', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ projectId }),
        });

        if (!response.ok) {
          throw new Error('Failed to increment pin count');
        }

        setIsPinned(true);
      } else {
        setError(result.reason || 'Failed to pin frame');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsPinning(false);
    }
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <Button
        onClick={handlePinFrame}
        disabled={isPinning || isPinned}
        className={className}
      >
        {isPinning ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Pinning...
          </>
        ) : isPinned ? (
          <>
            <Check className="mr-2 h-4 w-4" />
            Pinned!
          </>
        ) : (
          'Pin Frame'
        )}
      </Button>
      {error && (
        <p className="text-sm text-red-500">{error}</p>
      )}
    </div>
  );
}
