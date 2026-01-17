"use client";

import { createContext, useContext, useEffect, useRef, useState, useCallback } from "react";
import { DetectionEvent, SystemMetricEvent, AppEvent, EventType } from "../types/events";


interface WebSocketContextType {
  isConnected: boolean;
  subscribe: (cameraId: string | null, callback: (event: AppEvent) => void) => () => void;

}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

// Mock Data Generators (Moved/Adapted from page.tsx logic for consistency)
const mockMessages: Record<EventType, string[]> = {
  detection: ["Vehicle detected", "Pedestrian crossing", "Cyclist on road"],
  anomaly: ["Traffic congestion", "Stopped vehicle", "Debris on road"],
  alert: ["Speeding violation", "Red light violation"],
  system: ["System healthy", "Camera connected"],
};


function generateMockSystemEvent(): SystemMetricEvent {
  const types = ["cpu_usage", "memory_usage", "kafka_lag"] as const;
  const metricType = types[Math.floor(Math.random() * types.length)];
  
  let value = 0;
  let unit = "";
  let status: "healthy" | "warning" | "critical" = "healthy";
  let message = "";

  if (metricType === "cpu_usage") {
    value = Math.floor(Math.random() * 40) + 40; // 40-80% baseline
    if (Math.random() > 0.8) value += 15; // Spike
    unit = "%";
    if (value > 90) status = "critical";
    else if (value > 80) status = "warning";
    message = `CPU Load at ${value}%`;
  } else if (metricType === "memory_usage") {
     value = Math.floor(Math.random() * 30) + 50; // 50-80%
     unit = "%";
     if (value > 85) status = "warning";
     message = `Memory usage stable`;
  } else if (metricType === "kafka_lag") {
      value = Math.floor(Math.random() * 100); // 0-100ms lag
      if (Math.random() > 0.9) value += 500; // Lag spike
      unit = "ms";
      if (value > 1000) status = "critical";
      else if (value > 200) status = "warning";
      message = `Consumer lag: ${value}ms`;
  }

  return {
      id: `sys_${Date.now()}_${Math.random()}`,
      timestamp: new Date(),
      eventType: "system",
      metricType,
      value,
      unit,
      status,
      message
  };
}

function generateMockEvent(cameraId?: string): AppEvent {
  // 30% chance of system metric if no specific camera requested (or just broadcast generally)
  // But usually system metrics are global.
  // Let's keep `generateMockEvent` for camera events and a separate loop or mixed chance.
  
  const types: EventType[] = ["detection", "anomaly", "alert"];
  const type = types[Math.floor(Math.random() * types.length)];
  const msgs = mockMessages[type];
  
  // Random camera if not specified
  const targetCameraId = cameraId || `cam_0${Math.floor(Math.random() * 4) + 1}`;
  
  return {
    id: `evt_${Date.now()}_${Math.random()}`,
    timestamp: new Date(),
    cameraId: targetCameraId,
    cameraName: `Camera ${targetCameraId.split("_")[1]}`, // Simple mock name
    eventType: type,
    message: msgs[Math.floor(Math.random() * msgs.length)],
    detections: type === "detection" || type === "anomaly" ? [
       {
           class: "car",
           confidence: 0.85 + Math.random() * 0.14,
           bbox: [0.2 + Math.random() * 0.5, 0.2 + Math.random() * 0.5, 0.1 + Math.random() * 0.2, 0.1 + Math.random() * 0.2], // Normalized [x, y, w, h]
       }
    ] : undefined
  };
}

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [isConnected, setIsConnected] = useState(false);
  const subscribersRef = useRef<Map<string | null, Set<(event: AppEvent) => void>>>(new Map());
  const wsRef = useRef<WebSocket | null>(null);
  
  // Configuration
  const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
  const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_WS !== "false"; // Default to true if not explicitly false

  // Handle broadcasting to subscribers
  const broadcast = useCallback((event: AppEvent) => {
    // Notify "all cameras" subscribers (key: null)
    const wildCardSubs = subscribersRef.current.get(null);
    wildCardSubs?.forEach((cb) => cb(event));

    // Notify specific camera subscribers of camera events

    if (event.eventType !== "system" ) {
        const camEvent = event as DetectionEvent;
        const camSubs = subscribersRef.current.get(camEvent.cameraId);
        camSubs?.forEach((cb) => cb(event));
    }
  }, []);

  const subscribe = useCallback((cameraId: string | null, callback: (event: AppEvent) => void) => {
    if (!subscribersRef.current.has(cameraId)) {
      subscribersRef.current.set(cameraId, new Set());
    }
    subscribersRef.current.get(cameraId)!.add(callback);

    // Unsubscribe function
    return () => {
      const subs = subscribersRef.current.get(cameraId);
      subs?.delete(callback);
      if (subs?.size === 0) {
        subscribersRef.current.delete(cameraId);
      }
    };
  }, []);

  useEffect(() => {
    if (USE_MOCK) {
      console.log("[WebSocket] Using Mock Mode");
      setIsConnected(true);
      
      const interval = setInterval(() => {
        // Emit detection event
        const event = generateMockEvent();
        broadcast(event);
      }, 2000); 

      const sysInterval = setInterval(() => {
          const sysEvent = generateMockSystemEvent();
          broadcast(sysEvent);
      }, 3000); // System metrics every 3s

      return () => {
          clearInterval(interval);
          clearInterval(sysInterval);
      };
    } else {
        // Real WebSocket Implementation
        console.log(`[WebSocket] Connecting to ${WS_URL}...`);
        const ws = new WebSocket(WS_URL);

        ws.onopen = () => {
            console.log("[WebSocket] Connected");
            setIsConnected(true);
        };

        ws.onmessage = (msg) => {
            try {
                const data = JSON.parse(msg.data);
                // Transform raw data to DetectionEvent if needed
                // For now assuming backend sends matching shape or we map it here

                // We need to type guard this in real app
                const event = data as AppEvent;
                broadcast(event);
            } catch (err) {
                console.error("[WebSocket] Failed to parse message", err);
            }
        };

        ws.onclose = () => {
            console.log("[WebSocket] Disconnected");
            setIsConnected(false);
        };

        ws.onerror = (err) => {
            console.error("[WebSocket] Error", err);
            setIsConnected(false);
        };

        wsRef.current = ws;

        return () => {
            ws.close();
        };
    }
  }, [WS_URL, USE_MOCK, broadcast]);

  return (
    <WebSocketContext.Provider value={{ isConnected, subscribe }}>
      {children}
    </WebSocketContext.Provider>
  );
}

// Hook for consuming events
export function useWebSocket(cameraId?: string) {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error("useWebSocket must be used within a WebSocketProvider");
  }

  const [lastEvent, setLastEvent] = useState<AppEvent | null>(null);

  useEffect(() => {
    // Subscribe to specific camera or all (if undefined)
    // Note: Our Context.subscribe takes `null` for "all", so we pass `cameraId || null`
    const unsubscribe = context.subscribe(cameraId || null, (event) => {
      setLastEvent(event);
    });
    return unsubscribe;
  }, [context, cameraId]);

  return {
    isConnected: context.isConnected,
    lastEvent,
  };
}
