export interface TriageTask {
  id: string;
  imageUrl: string;
  currentLabel: string;
  confidence: number;
  bbox: [number, number, number, number]; // [x, y, w, h] normalized
}

// Backend response shape
interface BackendTriageItem {
  id: string;
  image_path: string;
  current_label: string | null;
  confidence: number | null;
  created_at: string;
  camera_id: string | null;
}

export const api = {
  fetchNextImage: async (): Promise<TriageTask | null> => {
    try {
      const res = await fetch("/api/triage/queue?limit=10", {
        headers: {
            "Cache-Control": "no-cache"
        }
      });
      if (!res.ok) throw new Error("Failed to fetch queue");
      
      const queue: BackendTriageItem[] = await res.json();
      if (queue.length === 0) return null;

      // Stick with the first item for now (simple queue)
      const item = queue[0];

      // MOCK ADAPTER LOGIC because backend lacks these fields
      // and we need them for the UI to be functional
      
      // 1. Generate random valid bbox if missing (always missing currently)
      const mockBbox: [number, number, number, number] = [
        0.2 + Math.random() * 0.4, // x: 20-60%
        0.2 + Math.random() * 0.4, // y: 20-60%
        0.2 + Math.random() * 0.2, // w: 20-40%
        0.2 + Math.random() * 0.2  // h: 20-40%
      ];

      // 2. Mock confidence if missing
      const mockConfidence = item.confidence ?? (0.6 + Math.random() * 0.39);

      // 3. Fallback label
      const label = item.current_label || "unknown";

      return {
        id: item.id,
        imageUrl: item.image_path, // Assumes image_path is accessible URL or proxy handles it
        currentLabel: label,
        confidence: mockConfidence,
        bbox: mockBbox,
      };

    } catch (error) {
        console.error("API Error:", error);
        throw error;
    }
  },

  submitValidation: async (id: string, verified: boolean, currentLabel: string = "unknown"): Promise<void> => {
    try {
        const body = {
            verified,
            correct_label: verified ? currentLabel : "rejected_class" // Basic handling for now
        };
        
        await fetch(`/api/triage/${id}/validate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

    } catch (error) {
        console.error("Validation Error:", error);
        throw error;
    }
  },
};
