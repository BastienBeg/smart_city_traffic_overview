# Epic 3: Mission Control Frontend

**Goal:** Create the Next.js visual dashboard to consume real-time events and stream video, serving as the primary operator interface.

## Story 3.1: Frontend Application Setup
**As a** Frontend Developer,
**I want** to initialize the Next.js application with the correct styling and directory structure,
**So that** I have a solid foundation for the UI components.

**Acceptance Criteria:**
- [ ] Next.js 14+ (App Router) initialized in `services/web-dashboard`.
- [ ] TailwindCSS configured with the "Cyberpunk" color palette (from `front-end-spec.md`).
- [ ] Project directory structure mirrors the standard feature-based architecture.
- [ ] Standard layout (Sidebar, Main Content Area) implemented.

## Story 3.2: Mission Control Dashboard Layout
**As a** City Operator,
**I want** to see a grid of all active cameras and a live event log on a single screen,
**So that** I have immediate situational awareness.

**Acceptance Criteria:**
- [ ] Responsive Grid Layout (scales from 1x1 to 4x4).
- [ ] Sidebar Navigation (Mission Control, Map, Triage, Settings).
- [ ] "Event Log" panel on the right side.
- [ ] Empty states defined for "No Cameras" or "No Events".

## Story 3.3: Video Player Component
**As a** User,
**I want** to view live video from the cameras within the dashboard,
**So that** I can track vehicles in real-time.

**Acceptance Criteria:**
- [ ] Component `VideoPlayer` created.
- [ ] Supports HLS playback (via `mediamtx` streams) or WebRTC.
- [ ] Handles Aspect Ratio correctly.
- [ ] Auto-reconnect on stream failure.
- [ ] "Loading" and "Offline" visual states implemented.

## Story 3.4: Real-time Visualizations (WebSockets + Canvas)
**As a** User,
**I want** to see bounding boxes drawn over the video feeds corresponding to detections,
**So that** I know exactly what the AI has identified.

**Acceptance Criteria:**
- [ ] Connect to Backend WebSocket endpoint for real-time events.
- [ ] Match `DetectionEvent` to the correct camera feed.
- [ ] Draw Bounding Boxes on a transparent `<canvas>` overlay on top of the video.
- [ ] Box color corresponds to confidence or class (e.g., Red for Anomalies, Green for Cars).

## Story 3.5: Event Log
**As a** Operator,
**I want** a scrolling list of recent detections and alerts for urgent anomalies,
**So that** I don't miss events that happen off-screen or briefly.

**Acceptance Criteria:**
- [ ] `EventLog` component showing timestamp, camera name, and event type.
- [ ] Critical Anomalies triggers a visual alert (e.g., row highlight).
- [ ] List auto-scrolls to new items (can be paused on hover).
- [ ] Clicking an event in the log highlights the relevant camera.

## Story 3.6: City Map Integration
**As a** City Operator,
**I want** to see a geographical map of the city with camera markers and traffic heatmaps,
**So that** I can spatially understand where incidents are happening and manage the network.

**Acceptance Criteria:**
- [ ] Map Library installed and `MapGl` component created.
- [ ] Camera Pins displayed at correct (Lat/Long).
- [ ] Pin color reflects Camera Status (Green/Red/Grey).
- [ ] Bi-directional linking: Click Pin -> View Cam; Click Cam -> Show on Map.

## Story 3.7: UI Polish & Real Camera Validation
**As a** Portfolio Presenter (and City Operator),
**I want** the dashboard to have polished, consistent styling and work with real public camera feeds,
**So that** the "Wow Factor" is achieved and Epic 3 is validated end-to-end.

**Acceptance Criteria:**
- [ ] All pages use consistent Cyberpunk CSS variables (no generic Tailwind).
- [ ] Sidebar and layout calculations are consistent across all pages.
- [ ] At least 2 real public traffic camera streams integrated and working.
- [ ] Cross-page navigation verified (Dashboard ↔ Map).

