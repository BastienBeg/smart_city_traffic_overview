"use client";

import { useState, useEffect } from "react";
import VideoGrid, { Camera } from "@/components/ui/VideoGrid";
import EventLog from "@/components/ui/EventLog";
import { HealthDashboard } from "@/components/ui/HealthDashboard";
import { DetectionEvent } from "@/types/events";

import { useWebSocket } from "@/contexts/WebSocketContext";

// Mock camera data
const mockCameras: Camera[] = [
  { id: "cam_01", name: "Main Intersection", status: "Live" },
  { id: "cam_02", name: "Highway Entry A", status: "Live" },
  { id: "cam_03", name: "Downtown Plaza", status: "Alert" },
  { id: "cam_04", name: "Industrial Zone", status: "Live" },
];

export default function MissionControlPage() {
  const [cameras] = useState<Camera[]>(mockCameras);
  const [events, setEvents] = useState<DetectionEvent[]>([]);
  const { lastEvent } = useWebSocket(); // Subscribe to all events

  // Update events log when new event arrives via WebSocket
  useEffect(() => {
    if (lastEvent && lastEvent.eventType !== "system") {
      setEvents((prev) => {
        // Keep last 50 events
        const newEvents = [...prev, lastEvent as DetectionEvent];
        if (newEvents.length > 50) {
            return newEvents.slice(newEvents.length - 50);
        }
        return newEvents;
      });
    }
  }, [lastEvent]);

  // Calculate stats
  const activeCameras = cameras.filter((c) => c.status === "Live").length;
  const alertCameras = cameras.filter((c) => c.status === "Alert").length;
  const anomalyCount = events.filter((e) => e.eventType === "anomaly").length;
  const detectionCount = events.filter((e) => e.eventType === "detection").length;

  return (
    <div className="h-screen flex">
      {/* Main Content Area - 80% (accounting for 5% sidebar handled by MainLayout) */}
      <div className="flex-1 flex flex-col p-6 overflow-hidden" style={{ width: "75%" }}>
        {/* Header with Stats */}
        <header className="mb-6 shrink-0">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-text-primary">
                Mission Control
              </h1>
              <p className="text-text-muted text-sm mt-1">
                Real-time traffic monitoring and anomaly detection
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 bg-success/20 text-success rounded-full text-sm font-medium">
                System Online
              </span>
            </div>
          </div>

          {/* Stats Bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              label="Active Cameras"
              value={activeCameras.toString()}
              status="success"
            />
            <StatCard
              label="Cameras in Alert"
              value={alertCameras.toString()}
              status={alertCameras > 0 ? "alert" : "success"}
            />
            <StatCard
              label="Detections"
              value={detectionCount.toString()}
              status="primary"
            />
            <StatCard
              label="Anomalies"
              value={anomalyCount.toString()}
              status={anomalyCount > 0 ? "warning" : "success"}
            />
          </div>
        </header>

        {/* Video Grid */}
        <div className="flex-1 overflow-auto bg-surface rounded-lg border border-text-muted/20">
          <VideoGrid cameras={cameras} />
        </div>
      </div>

      {/* Event Log Panel - 20% */}
      <div className="w-80 border-l border-text-muted/20 p-4 flex flex-col gap-4">
        <HealthDashboard />
        <EventLog events={events} maxHeight="calc(100vh - 350px)" />
      </div>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  status: "success" | "primary" | "alert" | "warning";
}

function StatCard({ label, value, status }: StatCardProps) {
  const statusColors = {
    success: "text-success border-success/30",
    primary: "text-primary border-primary/30",
    alert: "text-alert border-alert/30",
    warning: "text-warning border-warning/30",
  };

  return (
    <div className={`bg-surface rounded-lg p-4 border ${statusColors[status]}`}>
      <p className="text-text-muted text-xs uppercase tracking-wider">
        {label}
      </p>
      <p
        className={`text-2xl font-bold mt-1 ${statusColors[status].split(" ")[0]}`}
      >
        {value}
      </p>
    </div>
  );
}
