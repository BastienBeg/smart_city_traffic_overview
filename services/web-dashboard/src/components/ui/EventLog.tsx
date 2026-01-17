"use client";

import { useEffect, useRef, useState } from "react";
import { NoEventsEmptyState } from "./EmptyState";

import { DetectionEvent, EventType } from "@/types/events";

export interface EventLogProps {
  events: DetectionEvent[];
  maxHeight?: string;
}

const eventTypeConfig: Record<
  EventType,
  { bg: string; text: string; label: string }
> = {
  detection: {
    bg: "bg-primary/20",
    text: "text-primary",
    label: "Detection",
  },
  anomaly: {
    bg: "bg-alert/20",
    text: "text-alert",
    label: "Anomaly",
  },
  alert: {
    bg: "bg-warning/20",
    text: "text-warning",
    label: "Alert",
  },
  system: {
    bg: "bg-success/20",
    text: "text-success",
    label: "System",
  },
};

function formatTimestamp(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  if (diff < 60000) {
    const seconds = Math.floor(diff / 1000);
    return `${seconds}s ago`;
  }
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000);
    return `${minutes}m ago`;
  }
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function EventLog({
  events,
  maxHeight = "calc(100vh - 200px)",
}: EventLogProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);

  // Auto-scroll to bottom when new events arrive (unless hovered)
  useEffect(() => {
    if (containerRef.current && autoScroll && !isHovered) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [events, autoScroll, isHovered]);

  // Pause auto-scroll on hover
  const handleMouseEnter = () => {
    setIsHovered(true);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
  };

  // Resume auto-scroll when scrolled to bottom
  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
      setAutoScroll(isAtBottom);
    }
  };

  if (events.length === 0) {
    return (
      <div className="bg-surface rounded-lg border border-text-muted/20 h-full flex items-center justify-center">
        <NoEventsEmptyState />
      </div>
    );
  }

  return (
    <div className="bg-surface rounded-lg border border-text-muted/20 h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-text-muted/20 flex items-center justify-between">
        <h2 className="text-lg font-medium text-text-primary">Live Events</h2>
        <span className="text-xs text-text-muted">
          {autoScroll ? "Auto-scrolling" : "Paused"}
        </span>
      </div>

      {/* Events List */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto p-4 space-y-2"
        style={{ maxHeight }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onScroll={handleScroll}
      >
        {events.map((event) => {
          const config = eventTypeConfig[event.eventType];
          return (
            <div
              key={event.id}
              className="flex items-start gap-3 p-3 rounded-lg hover:bg-background/50 transition-colors border border-transparent hover:border-text-muted/10"
            >
              {/* Event Type Badge */}
              <span
                className={`shrink-0 px-2 py-0.5 rounded text-xs font-medium ${config.bg} ${config.text}`}
              >
                {config.label}
              </span>

              {/* Event Content */}
              <div className="flex-1 min-w-0">
                <p className="text-text-primary text-sm truncate">
                  {event.message}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-text-muted text-xs">
                    {event.cameraName}
                  </span>
                  <span className="text-text-muted/50 text-xs">•</span>
                  <span className="text-text-muted text-xs">
                    {formatTimestamp(event.timestamp)}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Resume Auto-scroll Button (when paused) */}
      {!autoScroll && (
        <div className="p-2 border-t border-text-muted/20">
          <button
            onClick={() => {
              setAutoScroll(true);
              if (containerRef.current) {
                containerRef.current.scrollTop =
                  containerRef.current.scrollHeight;
              }
            }}
            className="w-full py-2 text-xs text-primary hover:bg-primary/10 rounded transition-colors"
          >
            ↓ Resume auto-scroll
          </button>
        </div>
      )}
    </div>
  );
}
