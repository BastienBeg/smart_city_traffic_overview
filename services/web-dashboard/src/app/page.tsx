"use client";

import { useState, useEffect } from "react";
import VideoGrid from "@/components/ui/VideoGrid";
import { Camera } from "@/types/camera";
import EventLog from "@/components/ui/EventLog";
import { HealthDashboard } from "@/components/ui/HealthDashboard";
import { DetectionEvent } from "@/types/events";

import { useWebSocket } from "@/contexts/WebSocketContext";

// Mock camera data - includes real Iowa DOT cameras for validation
const mockCameras: Camera[] = [
  // Real cameras (matching Iowa DOT from Map page with actual HLS streams)
  { 
    id: "iowa-us20-jfk", 
    name: "US 20 at JFK Rd (Iowa DOT)", 
    location: { lat: 42.4920, lng: -92.3448 },
    status: "online",
    streamUrl: "https://iowadotsfs1.us-east-1.skyvdn.com:443/rtplive/dqtv17lb/playlist.m3u8"
  },
  { 
    id: "iowa-i80-280", 
    name: "I-80/I-280 Interchange (Iowa DOT)", 
    location: { lat: 41.5232, lng: -90.5150 },
    status: "online",
    streamUrl: "https://iowadotsfs1.us-east-1.skyvdn.com:443/rtplive/dqtv01lb/playlist.m3u8"
  },
  // Mock cameras (fallback to localhost mock server)
  { id: "cam_03", name: "Downtown Plaza", location: { lat: 37.7649, lng: -122.4294 }, status: "alert" },
  { id: "cam_04", name: "Industrial Zone", location: { lat: 37.7549, lng: -122.4394 }, status: "online" },
];

export default function MissionControlPage() {
  const [cameras] = useState<Camera[]>(mockCameras);
  const [events, setEvents] = useState<DetectionEvent[]>([]);
  const { lastEvent } = useWebSocket(); // Subscribe to all events

  // Update events log when new event arrives via WebSocket
  useEffect(() => {
    if (lastEvent && lastEvent.eventType !== "system") {
      // eslint-disable-next-line react-hooks/set-state-in-effect
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
  const activeCameras = cameras.filter((c) => c.status === "online").length;
  const alertCameras = cameras.filter((c) => c.status === "alert").length;
  const anomalyCount = events.filter((e) => e.eventType === "anomaly").length;
  const detectionCount = events.filter((e) => e.eventType === "detection").length;

  return (
    <div className="h-screen flex">
      {/* Main Content Area - Flexible width accounting for Event Log panel */}
      <div className="flex-1 flex flex-col p-6 overflow-hidden">
        {/* Header with Stats */}
        <header className="mb-6 shrink-0">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold font-orbitron text-primary tracking-wide glow-primary-text">
                Mission Control
              </h1>
              <p className="text-text-muted text-sm mt-1 font-mono">
                Real-time traffic monitoring and anomaly detection
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 bg-success/20 text-success rounded-full text-xs font-bold font-mono tracking-wider uppercase border border-success/30">
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
        <div className="flex-1 overflow-auto bg-surface/50 rounded-lg border border-text-muted/20 backdrop-blur-sm p-1">
          <VideoGrid cameras={cameras} />
        </div>
      </div>

      {/* Event Log Panel - Fixed width */}
      <div className="w-96 border-l border-text-muted/20 p-6 flex flex-col gap-6 bg-surface/30 backdrop-blur-md">
        <HealthDashboard />
        <EventLog events={events} maxHeight="calc(100vh - 400px)" />
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
    success: "text-success border-success/30 bg-success/5",
    primary: "text-primary border-primary/30 bg-primary/5",
    alert: "text-alert border-alert/30 bg-alert/5",
    warning: "text-warning border-warning/30 bg-warning/5",
  };

  return (
    <div className={`rounded-lg p-4 border transition-all hover:bg-opacity-20 ${statusColors[status]}`}>
      <p className="text-text-muted text-[10px] uppercase tracking-widest font-bold">
        {label}
      </p>
      <p
        className={`text-3xl font-bold mt-1 font-orbitron ${statusColors[status].split(" ")[0]}`}
      >
        {value}
      </p>
    </div>
  );
}
