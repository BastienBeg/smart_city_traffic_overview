"use client";

import { useEffect, useRef } from "react";
import { Detection } from "@/types/events";

interface VideoOverlayProps {
  detections: Detection[];
  width?: number;
  height?: number;
  isAnomaly?: boolean; // If true, draws all boxes in alert color
}

export default function VideoOverlay({
  detections,
  width = 640,
  height = 360,
  isAnomaly = false,
}: VideoOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Clear previous frame
    ctx.clearRect(0, 0, width, height);

    if (!detections || detections.length === 0) return;

    // Drawing settings
    const baseColor = isAnomaly ? "#FF2A6D" : "#00FF94"; // Cyberpunk Red or Green
    ctx.strokeStyle = baseColor;
    ctx.lineWidth = 2;
    ctx.font = "12px sans-serif";
    ctx.fillStyle = baseColor;

    detections.forEach((det) => {
      // bbox is [x, y, w, h] normalized
      const [nx, ny, nw, nh] = det.bbox;
      
      const x = nx * width;
      const y = ny * height;
      const w = nw * width;
      const h = nh * height;

      // Draw box
      ctx.strokeRect(x, y, w, h);

      // Draw label background
      const label = `${det.class} ${(det.confidence * 100).toFixed(0)}%`;
      const textMetrics = ctx.measureText(label);
      const textHeight = 12; // approx
      
      ctx.globalAlpha = 0.7;
      ctx.fillRect(x, y - textHeight - 4, textMetrics.width + 8, textHeight + 4);
      ctx.globalAlpha = 1.0;

      // Draw label text
      ctx.save();
      ctx.fillStyle = "#050505"; // Black text on colored bg
      ctx.fillText(label, x + 4, y - 4);
      ctx.restore();
    });

  }, [detections, width, height, isAnomaly]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      className="absolute inset-0 pointer-events-none w-full h-full"
      // w-full h-full ensures it stretches to container if width/height props are just for internal logic
      // But we should try to match internal resolution to render size for crispness
    />
  );
}
