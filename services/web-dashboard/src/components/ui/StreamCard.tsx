"use client";

import VideoPlayer from "./VideoPlayer";
import VideoOverlay from "./VideoOverlay";
import { useWebSocket } from "@/contexts/WebSocketContext";
import { useRef, useEffect, useState } from "react";

import { CameraStatus } from "@/types/camera";

// Helper component to connect overlay to WS to avoid bloating StreamCard
function ConnectedOverlay({ cameraId, isAnomaly }: { cameraId: string, isAnomaly: boolean }) {
    const { lastEvent } = useWebSocket(cameraId);
    const containerRef = useRef<HTMLDivElement>(null);
    const [dims, setDims] = useState({ w: 0, h: 0 });

    useEffect(() => {
        if (!containerRef.current) return;
        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                setDims({ w: entry.contentRect.width, h: entry.contentRect.height });
            }
        });
        resizeObserver.observe(containerRef.current);
        return () => resizeObserver.disconnect();
    }, []);

    const detections = (lastEvent && "detections" in lastEvent) ? lastEvent.detections || [] : [];


    return (
        <div ref={containerRef} className="w-full h-full">
            <VideoOverlay 
                detections={detections} 
                width={dims.w} 
                height={dims.h} 
                isAnomaly={isAnomaly || (lastEvent?.eventType === "anomaly")} 
            />
        </div>
    );
}

export interface StreamCardProps {
  cameraId: string;
  name: string;
  status: CameraStatus;
  thumbnailUrl?: string;
  streamUrl?: string;
}

export default function StreamCard({
  cameraId,
  name,
  status,
  thumbnailUrl,
  streamUrl,
}: StreamCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  const statusConfig = {
    online: {
      border: "border-success",
      glow: "glow-success",
      dot: "bg-success",
      text: "text-success",
    },
    offline: {
      border: "border-text-muted",
      glow: "",
      dot: "bg-text-muted",
      text: "text-text-muted",
    },
    alert: {
      border: "border-alert",
      glow: "glow-alert animate-pulse",
      dot: "bg-alert",
      text: "text-alert",
    },
  };

  const config = statusConfig[status];

  return (
    <div
      className={`relative aspect-video bg-background rounded-lg border-2 ${config.border} ${
        status === "alert" ? config.glow : ""
      } overflow-hidden transition-all duration-200 group cursor-pointer`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      data-camera-id={cameraId}
    >
      {/* Thumbnail/Video Placeholder */}
      {/* Video Player or Thumbnail */}
      {/* Video Player or Thumbnail */}
        {status === "online" || status === "alert" ? (
        <>
            <VideoPlayer 
                streamUrl={streamUrl || `http://localhost:8888/cam/${cameraId}/index.m3u8`}
                className="absolute inset-0 w-full h-full object-cover"
                // object-cover might conflict with player's internal sizing, but generic VideoPlayer has w/h 100%
            />
            {/* Overlay */}
            <div className="absolute inset-0 pointer-events-none z-10">
                 <ConnectedOverlay cameraId={cameraId} isAnomaly={status === "alert"} />
            </div>
        </>
      ) : thumbnailUrl ? (
        <img
          src={thumbnailUrl}
          alt={name}
          className="absolute inset-0 w-full h-full object-cover"
        />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center bg-zinc-900">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1}
            stroke="currentColor"
            className="w-12 h-12 text-text-muted/30"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z"
            />
          </svg>
        </div>
      )}

      {/* Status Indicator */}
      <div className="absolute top-2 right-2 flex items-center gap-1.5 px-2 py-1 bg-background/80 rounded-full backdrop-blur-sm">
        <span className={`w-2 h-2 rounded-full ${config.dot} ${status === "alert" ? "animate-pulse" : ""}`} />
        <span className={`text-xs font-medium ${config.text}`}>{status.toUpperCase()}</span>
      </div>

      {/* Camera Name Overlay */}
      <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-background/90 to-transparent">
        <p className="text-text-primary text-sm font-medium truncate">{name}</p>
        <p className="text-text-muted text-xs">{cameraId}</p>
      </div>

      {/* Hover Overlay */}
      <div
        className={`absolute inset-0 bg-primary/10 flex items-center justify-center transition-opacity duration-200 ${
          isHovered ? "opacity-100" : "opacity-0"
        }`}
      >
        <button
          className="px-4 py-2 bg-primary text-background font-medium rounded-lg hover:bg-primary/90 transition-colors transform hover:scale-105"
          onClick={(e) => {
            e.stopPropagation();
            // Expand functionality deferred to future story
            console.log(`Expand camera: ${cameraId}`);
          }}
        >
          <span className="flex items-center gap-2">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="w-4 h-4"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15"
              />
            </svg>
            Expand
          </span>
        </button>
      </div>
    </div>
  );
}
