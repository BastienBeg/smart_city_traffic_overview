"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import ReactPlayer from "react-player";

export interface VideoPlayerProps {
  streamUrl: string;
  className?: string; // Additional classes for the container
  aspectRatio?: string; // e.g., "16/9"
  onStatusChange?: (status: "loading" | "playing" | "error" | "offline") => void;
}

export default function VideoPlayer({
  streamUrl,
  className = "",
  aspectRatio = "16/9",
  onStatusChange,
}: VideoPlayerProps) {
  const [isMounted, setIsMounted] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  // Timeouts ref to clear on unmount
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Hydration fix
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsMounted(true);
    return () => {
      const timeout = reconnectTimeoutRef.current;
      if (timeout) {
        clearTimeout(timeout);
      }
    };
  }, []);

  const handleReady = useCallback(() => {
    setIsLoading(false);
    setError(false);
    setIsPlaying(true);
    setRetryCount(0); // Reset retries on success
    onStatusChange?.("playing");
  }, [onStatusChange]);

  const attemptReconnect = useCallback(() => {
    // Exponential backoff: 2^retryCount * 1000ms (max 30s)
    const delay = Math.min(Math.pow(2, retryCount) * 1000, 30000);
    console.log(`[VideoPlayer] Stream error. Retrying in ${delay}ms... (Attempt ${retryCount + 1})`);
    
    // Schedule retry
    reconnectTimeoutRef.current = setTimeout(() => {
      setError(false);
      setIsLoading(true);
      // Changing the key or forcing reload might be needed for some players, 
      // but ReactPlayer often handles re-mounting or prop updates. 
      // Here we just reset error/loading to trigger re-render/re-attempt.
      // If the URL is the same, ReactPlayer should try to reload it.
      setRetryCount((prev) => prev + 1);
    }, delay);

  }, [retryCount]);

  const handleError = useCallback(() => {
    setError(true);
    setIsLoading(false);
    setIsPlaying(false);
    onStatusChange?.("error");
    attemptReconnect();
  }, [onStatusChange, attemptReconnect]);

  const handleManualRetry = () => {
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    setRetryCount(0);
    setError(false);
    setIsLoading(true);
  };

  const handleBuffer = useCallback(() => {
    setIsLoading(true);
    onStatusChange?.("loading");
  }, [onStatusChange]);

  const handleBufferEnd = useCallback(() => {
    setIsLoading(false);
    onStatusChange?.("playing");
  }, [onStatusChange]);

  if (!isMounted) return null;

  return (
    <div
      className={`relative w-full overflow-hidden bg-black rounded-lg ${className}`}
      style={{ aspectRatio: aspectRatio.replace(":", "/") }}
    >
      {/* Loading & Error Overlays */}
      {(isLoading || error) && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-zinc-900/80 text-white backdrop-blur-sm">
          {error ? (
            <div className="flex flex-col items-center gap-4 text-red-500 animate-in fade-in zoom-in duration-300">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className="w-10 h-10"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z"
                />
              </svg>
              <div className="text-center">
                <span className="block text-sm font-semibold">Signal Lost</span>
                <span className="text-xs text-zinc-400">
                   Retrying in {Math.min(Math.pow(2, retryCount), 30)}s...
                </span>
              </div>
              <button 
                onClick={handleManualRetry}
                className="px-4 py-2 text-xs font-medium text-white bg-red-600 rounded hover:bg-red-700 transition-colors"
              >
                Retry Now
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3 text-zinc-400">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <span className="text-sm font-medium">Connecting...</span>
            </div>
          )}
        </div>
      )}

      {/* ReactPlayer Instance */}
      {/* Key forces re-mount on retry count allows "hard retry" if props don't trigger it */}
      <ReactPlayer
        key={`player-${retryCount}`}
        url={streamUrl}
        width="100%"
        height="100%"
        playing={isPlaying}
        controls={true}
        onReady={handleReady}
        onBuffer={handleBuffer}
        onBufferEnd={handleBufferEnd}
        onError={handleError}
        style={{ position: "absolute", top: 0, left: 0 }}
        config={{
            file: {
                forceHLS: true,
            }
        }}
      />
    </div>
  );
}
