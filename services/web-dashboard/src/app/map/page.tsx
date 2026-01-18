'use client';

import { Suspense } from 'react';
import dynamic from 'next/dynamic';
import { Camera } from '@/types/camera';

const CityMap = dynamic(() => import('@/components/ui/CityMap'), { 
  ssr: false,
  loading: () => (
    <div className="h-full w-full flex items-center justify-center bg-surface/50 text-text-muted">
       <div className="flex flex-col items-center gap-2">
           <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"/>
           <span>Initializing Map Engine...</span>
       </div>
    </div>
  )
});

// Camera Data - Mix of real public cameras and mock data
// Real cameras: Iowa DOT public traffic cameras (HLS streams)
// Mock cameras: San Francisco area for demo purposes
const CAMERAS: Camera[] = [
  // --- REAL PUBLIC CAMERAS (Iowa DOT) ---
  {
    id: 'iowa-us20-jfk',
    name: 'US 20 at JFK Rd - West (Iowa DOT)',
    location: { lat: 42.4920, lng: -92.3448 }, // Waterloo, Iowa
    status: 'online',
    lastUpdate: new Date().toISOString(),
    streamUrl: 'https://iowadotsfs1.us-east-1.skyvdn.com:443/rtplive/dqtv17lb/playlist.m3u8'
  },
  {
    id: 'iowa-i80-280',
    name: 'I-80/I-280 Interchange (Iowa DOT)',
    location: { lat: 41.5232, lng: -90.5150 }, // Davenport, Iowa
    status: 'online',
    lastUpdate: new Date().toISOString(),
    streamUrl: 'https://iowadotsfs1.us-east-1.skyvdn.com:443/rtplive/dqtv01lb/playlist.m3u8'
  },
  // --- MOCK CAMERAS (San Francisco area) ---
  {
    id: 'cam-003',
    name: 'Main St. Bridge',
    location: { lat: 37.7649, lng: -122.4294 },
    status: 'online',
    lastUpdate: '2024-05-20T09:55:00Z',
    streamUrl: '/streams/cam-003'
  },
  {
    id: 'cam-004',
    name: 'City Park South',
    location: { lat: 37.7549, lng: -122.4394 },
    status: 'offline',
    lastUpdate: '2024-05-19T20:00:00Z',
    streamUrl: '/streams/cam-004'
  }
];

export default function MapPage() {
  return (
    <div className="flex flex-col gap-6 p-6 h-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-wide text-primary font-orbitron glow-primary-text">City Map Overview</h1>
          <p className="text-text-muted mt-1 font-mono text-sm">Geospatial view of traffic camera network</p>
        </div>
      </div>
      
      <div className="flex-1 min-h-[600px] bg-surface rounded-lg border border-text-muted/20 shadow-sm p-4">
        <Suspense fallback={<div className="flex items-center justify-center h-full text-text-primary">Loading map data...</div>}>
            <CityMap cameras={CAMERAS} />
        </Suspense>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {['online', 'alert', 'offline'].map(status => {
           const count = CAMERAS.filter(c => c.status === status).length;
           const colorClass = status === 'online' ? 'text-success' : status === 'alert' ? 'text-alert' : 'text-text-muted';
           return (
             <div key={status} className="bg-surface/50 p-4 rounded-lg border border-text-muted/20 flex items-center justify-between">
               <span className="capitalize font-medium text-text-primary">{status}</span>
               <span className={`text-2xl font-bold ${colorClass}`}>{count}</span>
             </div>
           )
        })}
      </div>
    </div>
  );
}
