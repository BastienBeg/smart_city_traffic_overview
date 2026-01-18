import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, Mock } from "vitest";
import TriageInterface from "../TriageInterface";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock api
vi.mock("@/lib/api", () => ({
  api: {
    fetchNextImage: vi.fn(),
    submitValidation: vi.fn(),
  },
}));

import { api } from "@/lib/api";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe("TriageInterface", () => {
  let queryClient: QueryClient;

  // Mock task data
  const mockTask = {
    id: "task_123",
    imageUrl: "https://example.com/image.jpg",
    currentLabel: "car",
    confidence: 0.95,
    bbox: [0.1, 0.1, 0.2, 0.2] as [number, number, number, number],
  };

  beforeEach(() => {
    queryClient = createTestQueryClient();
    vi.clearAllMocks();
    (api.fetchNextImage as Mock).mockResolvedValue(mockTask);
    (api.submitValidation as Mock).mockResolvedValue(undefined);
  });

  const renderComponent = () =>
    render(
      <QueryClientProvider client={queryClient}>
        <TriageInterface />
      </QueryClientProvider>
    );

  it("renders loading state initially", () => {
    (api.fetchNextImage as Mock).mockImplementation(() => new Promise(() => {})); // Never resolves
    renderComponent();
    expect(screen.getByText("Fetching task...")).toBeInTheDocument();
  });

  it("renders task data when loaded", async () => {
    renderComponent();
    
    await waitFor(() => {
        expect(screen.getByText("TRIAGE STATION")).toBeInTheDocument();
    });

    expect(screen.getByText("car")).toBeInTheDocument();
    expect(screen.getByText("95.0%")).toBeInTheDocument();
    // Image alt text
    expect(screen.getByAltText("Triage Task")).toBeInTheDocument();
  });

  it("validates on Y key press", async () => {
    renderComponent();
    await waitFor(() => screen.getByText("car"));

    fireEvent.keyDown(window, { key: "y" });

    // Expect Verified feedback overlay (async)
    await waitFor(() => {
        expect(screen.getByText("Verified")).toBeInTheDocument();
    });

    // Expect API call after delay
    await waitFor(() => {
        expect(api.submitValidation).toHaveBeenCalledWith("task_123", true, "car");
    }, { timeout: 1000 });
  });

  it("rejects on N key press", async () => {
    renderComponent();
    await waitFor(() => screen.getByText("car"));

    fireEvent.keyDown(window, { key: "n" });

    // Expect Rejected feedback overlay
    await waitFor(() => {
        expect(screen.getByText("Rejected")).toBeInTheDocument();
    });

    // Expect API call
    await waitFor(() => {
        expect(api.submitValidation).toHaveBeenCalledWith("task_123", false, "car");
    }, { timeout: 1000 });
  });

   it("skips on Space key press", async () => {
    renderComponent();
    await waitFor(() => screen.getByText("car"));

    fireEvent.keyDown(window, { key: " " });

    // Should invalidate queries (fetch next) usage check is hard on queryClient directly here without spying prototype, 
    // but we can check if fetchNextImage called again? 
    // Actually React Query refetch might not happen instantly if stale time 0 but we mocked it.
    // Let's just check submitValidation is NOT called.
    
    await new Promise(r => setTimeout(r, 300));
    expect(api.submitValidation).not.toHaveBeenCalled();
  });
});
