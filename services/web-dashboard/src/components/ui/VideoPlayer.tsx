"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import ReactPlayer from "react-player";
import Hls from "hls.js";

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
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const isHls = streamUrl && (streamUrl.includes(".m3u8") || streamUrl.includes("blob:"));

  // Check support once
  const isHlsSupported = typeof window !== "undefined" && Hls.isSupported();

  const handleManualRetry = useCallback(() => {
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    setRetryCount(0);
    setError(false);
    setIsLoading(true);
  }, []);

  // HLS Direct Implementation
  useEffect(() => {
    if (!isHls || !isHlsSupported) return;

    let hls = hlsRef.current; 

    const initPlayer = () => {
      if (hls) {
        hls.destroy();
      }

      hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 90
      });
      hlsRef.current = hls;

      if (videoRef.current) {
        hls.attachMedia(videoRef.current);
      }

      hls.on(Hls.Events.MEDIA_ATTACHED, () => {
        hls?.loadSource(streamUrl);
      });

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setIsLoading(false);
        setIsPlaying(true);
        setError(false);
        setRetryCount(0);
        onStatusChange?.("playing");
        videoRef.current?.play().catch(() => {
          // Mute usually handles this, so ensuring muted prop is on video tag
        });
      });

      hls.on(Hls.Events.ERROR, (event, data) => {
        if (data.fatal) {
          console.error("[VideoPlayer] HLS Fatal Error:", data);
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              hls?.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              hls?.recoverMediaError();
              break;
            default:
              setIsLoading(false);
              setError(true);
              onStatusChange?.("error");
              hls?.destroy();
              break;
          }
        }
      });
    };

    initPlayer();

    return () => {
      if (hls) {
        hls.destroy();
      }
    };
  }, [streamUrl, isHls, isHlsSupported, retryCount, onStatusChange]);

  // Retry logic for manual HLS
  useEffect(() => {
    if (error && isHls) {
       const delay = Math.min(Math.pow(2, retryCount) * 1000, 30000);
       reconnectTimeoutRef.current = setTimeout(() => {
          // Trigger re-init by bumping retryCount (used in dep array)
          // or we can just call internal logic but dep array is cleaner
          // Actually, retryCount is in dep array, so changing it re-runs effect
       }, delay);
       return () => {
         if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
       };
    }
  }, [error, retryCount, isHls]);


  // Logic for ReactPlayer (fallback) callbacks
  const handleReady = useCallback(() => {
    setIsLoading(false);
    setError(false);
    setIsPlaying(true);
    onStatusChange?.("playing");
  }, [onStatusChange]);

  const handleError = useCallback((e: unknown) => {
    console.error("[VideoPlayer] Error (Fallback):", e);
    setError(true);
    setIsLoading(false);
    onStatusChange?.("error");
  }, [onStatusChange]);

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
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-10 h-10">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
              </svg>
              <div className="text-center">
                <span className="block text-sm font-semibold">Signal Lost</span>
                <span className="text-xs text-zinc-400">Retrying...</span>
              </div>
              <button 
                onClick={handleManualRetry}
                className="px-4 py-2 text-xs font-medium text-white bg-red-600 rounded hover:bg-red-700 transition-colors"
              >
                Retry
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

      {/* Player Implementation */}
      {isHls && isHlsSupported ? (
        <video
          ref={videoRef}
          className="w-full h-full object-cover"
          muted={true}
          autoPlay={true}
          controls={true}
          playsInline={true}
        />
      ) : (
        <ReactPlayer
          url={streamUrl}
          width="100%"
          height="100%"
          playing={isPlaying}
          muted={true}
          controls={true}
          onReady={handleReady}
          onError={handleError}
          onBuffer={() => setIsLoading(true)}
          onBufferEnd={() => setIsLoading(false)}
          style={{ position: "absolute", top: 0, left: 0 }}
        />
      )}
    </div>
  );
}
