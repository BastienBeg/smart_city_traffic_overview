"use client";

import { useEffect, useState } from "react";
import StreamCard, { CameraStatus } from "./StreamCard";
import { NoCamerasEmptyState } from "./EmptyState";

export interface Camera {
  id: string;
  name: string;
  status: CameraStatus;
  thumbnailUrl?: string;
}

export interface VideoGridProps {
  cameras: Camera[];
}

/**
 * Calculates grid columns based on camera count
 * - 1 camera: 1x1
 * - 2-4 cameras: 2x2
 * - 5-9 cameras: 3x3
 * - 10-16 cameras: 4x4
 */
function getGridColumns(count: number): number {
  if (count <= 1) return 1;
  if (count <= 4) return 2;
  if (count <= 9) return 3;
  return 4;
}

export default function VideoGrid({ cameras }: VideoGridProps) {
  const [width, setWidth] = useState(0);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setWidth(window.innerWidth);

    const handleResize = () => {
      setWidth(window.innerWidth);
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Calculate generic columns
  const baseCols = getGridColumns(cameras.length);
  
  // Apply responsive constraints
  let gridCols = baseCols;
  if (mounted) {
      if (width < 768) {
        gridCols = Math.min(baseCols, 1);
      } else if (width < 1024) {
        gridCols = Math.min(baseCols, 2);
      }
  } else {
      // Default for SSR/initial render
      gridCols = 1;
  }

  if (cameras.length === 0) {
    return (
      <div className="bg-surface rounded-lg border border-text-muted/20 min-h-[400px] flex items-center justify-center">
        <NoCamerasEmptyState />
      </div>
    );
  }

  return (
    <div
      className="grid gap-4 p-4"
      style={{
        gridTemplateColumns: `repeat(${gridCols}, minmax(0, 1fr))`,
      }}
    >
      {cameras.map((camera) => (
        <StreamCard
          key={camera.id}
          cameraId={camera.id}
          name={camera.name}
          status={camera.status}
          thumbnailUrl={camera.thumbnailUrl}
        />
      ))}
    </div>
  );
}
