"use client";

import React, { useEffect, useState } from "react";
import { Gauge } from "./Gauge"; // Adjust path if needed
import { useWebSocket } from "@/contexts/WebSocketContext"; // Adjust path if needed (src/contexts or src/context)
import { SystemMetricEvent } from "@/types/events";

interface SystemMetrics {
  cpu: { value: number; status: "healthy" | "warning" | "critical" };
  memory: { value: number; status: "healthy" | "warning" | "critical" };
  kafkaLag: { value: number; status: "healthy" | "warning" | "critical" };
}

export function HealthDashboard() {
  // Use global subscription (no cameraId)
  const { lastEvent } = useWebSocket();
  
  const [metrics, setMetrics] = useState<SystemMetrics>({
    cpu: { value: 0, status: "healthy" },
    memory: { value: 0, status: "healthy" },
    kafkaLag: { value: 0, status: "healthy" },
  });

  useEffect(() => {
    if (!lastEvent || lastEvent.eventType !== "system") return;

    const sysEvent = lastEvent as SystemMetricEvent;
    
    setMetrics((prev) => {
      const newMetrics = { ...prev };
      
      if (sysEvent.metricType === "cpu_usage") {
        newMetrics.cpu = { value: sysEvent.value, status: sysEvent.status };
      } else if (sysEvent.metricType === "memory_usage") {
        newMetrics.memory = { value: sysEvent.value, status: sysEvent.status };
      } else if (sysEvent.metricType === "kafka_lag") {
        newMetrics.kafkaLag = { value: sysEvent.value, status: sysEvent.status };
      }
      
      return newMetrics;
    });
  }, [lastEvent]);

  return (
    <div className="bg-gray-900/80 backdrop-blur-md border border-gray-800 rounded-xl p-4 shadow-2xl">
      <h3 className="text-lg font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 mb-4 tracking-wider uppercase">
        System Health
      </h3>
      
      <div className="flex flex-row items-center justify-around gap-4 flex-wrap">
        <Gauge 
          value={metrics.cpu.value} 
          status={metrics.cpu.status}
          label="CPU Load" 
          unit="%" 
        />
        <Gauge 
          value={metrics.memory.value} 
          status={metrics.memory.status}
          label="Memory" 
          unit="%" 
        />
        <Gauge 
          value={metrics.kafkaLag.value} 
          status={metrics.kafkaLag.status}
          label="Kafka Lag" 
          unit="ms"
          max={1000} // Scale lag explicitly if needed, or let Gauge handle
        />
      </div>
    </div>
  );
}
