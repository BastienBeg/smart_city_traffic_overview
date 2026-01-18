# AI UI Generation Prompt (for v0.dev / Lovable)

Copy and paste the following block into your AI UI tool of choice.

---

**High-Level Goal:**
Create a high-fidelity "Cyberpunk Control Center" dashboard for a Smart City Traffic Sentinel system. The interface must be dark, high-contrast, and dense with information, suitable for a 1080p+ monitoring screen. It features a responsive video grid, a real-time event log, and a specialized "Triage Mode" for validating AI detections.

**Tech Stack:**
*   Framework: React / Next.js
*   Styling: Tailwind CSS
*   Icons: Lucide React
*   Fonts: Inter (Google Fonts)

**Visual Style (Cyberpunk Modern):**
*   **Background:** Deep Navy/Black (`#050510`)
*   **Surface Cards:** Dark Blue (`#1A1A2E`)
*   **Primary Accent:** Neon Cyan (`#00F0FF`) - use for focus states and primary actions.
*   **Status Colors:**
    *   **Success:** Neon Green (`#00FF94`) - Healthy streams.
    *   **Alert:** Neon Red (`#FF2A6D`) - Anomalies/Errors.
    *   **Warning:** Amber (`#FFC857`).
*   **Typography:** `Inter` font. Use Uppercase + Tracking-widest for headers/labels.

**Step-by-Step Instructions:**

1.  **Layout Structure:**
    *   Create a Sidebar Navigation (Left, fixed width 64px). Icons: Grid (Mission Control), Map (City Map), CheckSquare (Triage), Activity (Pipeline), Settings.
    *   Add a "Notification Badge" (Red dot with number) to the Triage icon.
    *   Main Content Area fills the rest of the screen.

2.  **Screen 1: Mission Control (Dashboard):**
    *   **Top Bar:** Display system health metrics (CPU: 45%, Memory: 2.1GB, Kafka Lag: 0ms) using small sparkling/pulse animations to show key values.
    *   **Video Grid:** Create a responsive grid (auto-fit, min-width 300px).
    *   **Video Card Component:**
        *   Dark card background.
        *   Placeholder for video stream (gray rectangle).
        *   Overlay text (Top Left): "Camera-01 [LIVE]".
        *   Status Indicator (Top Right): Green pulsing dot.
        *   **Interaction:** On Hover, show an "Expand" button in the center.
        *   **Alert State:** If status is "Alert", add a pulsing Red border (`border-red-500 animate-pulse`).
    *   **Event Log (Right Panel):** A vertical list of text events (e.g., "10:42:05 - Stopped Vehicle detected @ Main St"). Use a monospace font for the timestamp.

3.  **Screen 2: Triage Station:**
    *   **Layout:** Focused "Single Task" view.
    *   **Center:** A large placeholder image (aspect video) representing the detected anomaly.
    *   **Controls (Bottom):** Large, touch-friendly buttons for rapid validation.
        *   Left Button (Red): "Reject (Left Arrow)".
        *   Right Button (Green): "Confirm (Right Arrow)".
        *   Middle Button (Gray): "Skip (Down Arrow)".
    *   **Progress Bar:** Top right showing "Batch Progress: 4/50".

4.  **Components & Micro-interactions:**
    *   Use `framer-motion` (or CSS transitions) for smooth hover effects.
    *   Buttons should have a "Glassmorphism" effect with a slight neon glow on hover.
    *   The Map view (if possible to mock) should look like a dark-mode vector map.

**Data Structures / Constraints:**
*   Do NOT use light mode. This is strictly dark mode.
*   Maximize screen real estate. Small padding, compact text.
*   The "Bridge" concept: Clicking an "Alert" item in the Event Log should simulate navigating to a Map View (just mock the state change).

**Scope:**
*   Generate the Shell (Navigation), the Dashboard View, and the Triage View.
*   Mock data is fine for the video feeds and logs.

---
