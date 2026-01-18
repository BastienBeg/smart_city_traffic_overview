"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, useCallback } from "react";
import Image from "next/image";
import { api } from "@/lib/api";

export default function TriageInterface() {
  const queryClient = useQueryClient();
  const [feedback, setFeedback] = useState<"correct" | "incorrect" | null>(null);
  const [validatedCount, setValidatedCount] = useState(0);

  // Fetch next image
  const { data: task, isLoading, isError, refetch } = useQuery({
    queryKey: ["triage", "next"],
    queryFn: api.fetchNextImage,
    staleTime: 0, // Always fetch fresh task
    gcTime: 0, // Don't cache for long
    refetchOnWindowFocus: false,
  });

  // Prefetch next task to ensure low latency (simple approach: just invalidate/refetch on completion)
  // Ideally we'd have a queue, but for now we'll just refetch immediately.

  const mutation = useMutation({
    mutationFn: async ({ id, verified, currentLabel }: { id: string; verified: boolean; currentLabel: string }) => {
      await api.submitValidation(id, verified, currentLabel);
    },
    onSuccess: () => {
      setValidatedCount((prev) => prev + 1);
      // Invalidate query to fetch next image
      queryClient.invalidateQueries({ queryKey: ["triage", "next"] });
      setFeedback(null);
    },
  });

  const handleValidation = useCallback((verified: boolean) => {
    if (!task || mutation.isPending) return;
    
    setFeedback(verified ? "correct" : "incorrect");
    
    // Short delay for visual feedback before fetching next
    setTimeout(() => {
        mutation.mutate({ id: task.id, verified, currentLabel: task.currentLabel });
    }, 200);
  }, [task, mutation]);

  const handleSkip = useCallback(() => {
      if (mutation.isPending) return;
      queryClient.invalidateQueries({ queryKey: ["triage", "next"] });
  }, [mutation, queryClient]);

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case "ArrowRight":
        case "y":
        case "Y":
          handleValidation(true);
          break;
        case "ArrowLeft":
        case "n":
        case "N":
          handleValidation(false);
          break;
        case "ArrowDown":
        case " ": // Space
          handleSkip();
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleValidation, handleSkip]);


  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-primary animate-pulse">
        Fetching task...
      </div>
    );
  }

  if (isError || !task) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-text-muted gap-4">
        <p>Failed to load task or queue empty.</p>
        <button 
            onClick={() => refetch()}
            className="px-4 py-2 bg-primary text-background rounded hover:bg-primary/90"
        >
            Retry
        </button>
      </div>
    );
  }

  // Calculate overlay position
  // task.bbox is [x, y, w, h] normalized
  const [bx, by, bw, bh] = task.bbox;
  const overlayStyle = {
    left: `${bx * 100}%`,
    top: `${by * 100}%`,
    width: `${bw * 100}%`,
    height: `${bh * 100}%`,
  };

  const getBorderColor = () => {
      if (feedback === "correct") return "border-green-500 shadow-[0_0_50px_rgba(34,197,94,0.5)]";
      if (feedback === "incorrect") return "border-red-500 shadow-[0_0_50px_rgba(239,68,68,0.5)]";
      return "border-primary/30";
  };

  return (
    <div className="flex flex-col h-full max-h-[calc(100vh-6rem)] gap-6 p-4">
        {/* Header / Stats */}
        <div className="flex justify-between items-center bg-background-paper p-4 rounded-lg border border-primary/20">
            <h2 className="text-xl font-orbitron text-primary">TRIAGE STATION</h2>
            <div className="flex gap-6 text-sm">
                <div className="flex flex-col items-end">
                    <span className="text-text-muted">SESSION VALIDATED</span>
                    <span className="text-xl font-bold text-text-primary">{validatedCount}</span>
                </div>
                 <div className="flex flex-col items-end">
                    <span className="text-text-muted">TARGET</span>
                    <span className="text-xl font-bold text-text-primary">50</span>
                </div>
            </div>
        </div>

        {/* Main Interface */}
        <div className="flex-1 flex gap-6 min-h-0">
            {/* Image Area */}
            <div className={`relative flex-1 bg-black rounded-lg border-2 overflow-hidden transition-all duration-200 ${getBorderColor()}`}>
                <Image 
                    src={task.imageUrl}
                    alt="Triage Task" 
                    fill
                    className="object-contain"
                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 70vw, 50vw"
                    priority
                />
                
                {/* Bounding Box Overlay */}
                <div 
                    className="absolute border-2 border-yellow-400 bg-yellow-400/10 pointer-events-none transition-all duration-300"
                    style={overlayStyle}
                >
                    <div className="absolute -top-7 left-0 bg-yellow-400 text-black text-xs font-bold px-1.5 py-0.5 shadow-sm">
                        {task.currentLabel.toUpperCase()} {(task.confidence * 100).toFixed(0)}%
                    </div>
                </div>

                {/* Feedback Overlay */}
                {feedback && (
                     <div className={`absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm animate-in fade-in duration-200`}>
                        {feedback === "correct" ? (
                            <div className="text-6xl font-black text-green-500 tracking-widest uppercase drop-shadow-[0_0_20px_rgba(34,197,94,0.8)]">Verified</div>
                        ) : (
                             <div className="text-6xl font-black text-red-500 tracking-widest uppercase drop-shadow-[0_0_20px_rgba(239,68,68,0.8)]">Rejected</div>
                        )}
                     </div>
                )}
            </div>

            {/* Controls / Info */}
            <div className="w-80 flex flex-col gap-4">
                <div className="bg-background-paper p-6 rounded-lg border border-primary/20 flex-1 flex flex-col justify-center items-center text-center gap-4">
                    <div className="text-text-muted uppercase text-xs tracking-wider">Current Detection</div>
                    <div className="text-4xl font-bold text-primary font-orbitron">{task.currentLabel}</div>
                    <div className="text-2xl text-text-secondary font-mono">{(task.confidence * 100).toFixed(1)}%</div>
                </div>

                {/* Keyboard Guide */}
                 <div className="bg-background-paper p-4 rounded-lg border border-primary/20">
                    <div className="space-y-3">
                        <div className="flex items-center justify-between group">
                            <div className="flex items-center gap-2">
                                <kbd className="px-2 py-1 bg-background border border-text-muted/30 rounded text-xs font-mono text-text-primary">Right / Y</kbd>
                                <span className="text-sm text-text-secondary">Validate</span>
                            </div>
                            <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50 group-hover:bg-green-500 transition-colors"></div>
                        </div>
                         <div className="flex items-center justify-between group">
                            <div className="flex items-center gap-2">
                                <kbd className="px-2 py-1 bg-background border border-text-muted/30 rounded text-xs font-mono text-text-primary">Left / N</kbd>
                                <span className="text-sm text-text-secondary">Reject</span>
                            </div>
                            <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50 group-hover:bg-red-500 transition-colors"></div>
                        </div>
                         <div className="flex items-center justify-between group">
                            <div className="flex items-center gap-2">
                                <kbd className="px-2 py-1 bg-background border border-text-muted/30 rounded text-xs font-mono text-text-primary">Space</kbd>
                                <span className="text-sm text-text-secondary">Skip</span>
                            </div>
                            <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50 group-hover:bg-yellow-500 transition-colors"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
  );
}
