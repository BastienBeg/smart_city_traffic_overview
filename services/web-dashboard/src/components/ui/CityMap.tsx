'use client';

import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { Camera } from '@/types/camera';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';

// Custom hook to handle map recentering when selectedCamera changes
function MapController({ selectedCamera }: { selectedCamera: Camera | null }) {
  const map = useMap();
  
  useEffect(() => {
    if (selectedCamera) {
      map.flyTo([selectedCamera.location.lat, selectedCamera.location.lng], 15, {
        animate: true,
        duration: 1.5
      });
    }
  }, [selectedCamera, map]);
  
  return null;
}

interface CityMapProps {
  cameras: Camera[];
}

const CityMap: React.FC<CityMapProps> = ({ cameras }) => {
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);
  const searchParams = useSearchParams();
  const cameraIdParam = searchParams.get('camera_id');

  // Load Leaflet assets fix (client-side only)
  useEffect(() => {
    // Fix leafleft default icon issues in Next.js
    // Unused vars removed
    // const iconRetinaUrl = '/images/marker-icon-2x.png'; ...

    // We can just rely on setting the default locally or overriding specific markers
    // But overriding the global prototype is effective for all markers
    
    // Check if window is defined just in case
    if (typeof window !== 'undefined') {
       // eslint-disable-next-line @typescript-eslint/no-explicit-any
       delete (L.Icon.Default.prototype as any)._getIconUrl;
       L.Icon.Default.mergeOptions({
         iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
         iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
         shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
       });
    }
  }, []);

  useEffect(() => {
    if (cameraIdParam) {
      const targetCamera = cameras.find(c => c.id === cameraIdParam);
      if (targetCamera) {
             // eslint-disable-next-line react-hooks/set-state-in-effect
            setSelectedCamera(targetCamera);
      }
    }
  }, [cameraIdParam, cameras]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-success bg-success/20 border-success';
      case 'alert': return 'text-alert bg-alert/20 border-alert animate-pulse';
      case 'offline': return 'text-text-muted bg-text-muted/20 border-text-muted';
      default: return 'text-primary bg-primary/20 border-primary';
    }
  };

  // Center on first camera or a default location (e.g., Iowa / Des Moines) if list empty
  const initialCenter: [number, number] = cameras.length > 0 
    ? [cameras[0].location.lat, cameras[0].location.lng] 
    : [41.5868, -93.6250]; // Des Moines approx

  return (
    <div className="w-full h-[600px] rounded-lg overflow-hidden border border-text-muted/20 relative">
       {/* List Side Panel (Desktop only or floating?) -> Let's keep it overlay or separate? 
           The previous design had a list. Let's make it a side panel or overlay.
           For "Polished", let's use a split view or just the map with a floating list.
           Given constraints, let's make the map dominant and put a floating list on the left.
       */}
       
       <MapContainer 
          center={initialCenter} 
          zoom={10} 
          scrollWheelZoom={true} 
          className="w-full h-full z-0"
          style={{ background: '#0f172a' }} // Dark background matching theme
       >
         <TileLayer
           attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
           url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
           // Dark mode filter for tiles to match Cyberpunk theme
           className="map-tiles-dark" 
         />
         
         <MapController selectedCamera={selectedCamera} />

         {cameras.map((camera) => (
           <Marker 
             key={camera.id} 
             position={[camera.location.lat, camera.location.lng]}
             eventHandlers={{
                click: () => setSelectedCamera(camera),
             }}
           >
             <Popup className="cyberpunk-popup">
               <div className="p-2 min-w-[200px]">
                 <h4 className="font-orbitron font-bold text-lg text-primary mb-1">{camera.name}</h4>
                 <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-0.5 rounded text-xs uppercase font-bold ${getStatusColor(camera.status)}`}>
                        {camera.status}
                    </span>
                    <span className="text-xs text-text-muted">ID: {camera.id}</span>
                 </div>
                 {camera.status === 'alert' && (
                    <button className="w-full mt-2 bg-alert text-black font-bold py-1 px-3 rounded hover:bg-alert/80 text-xs">
                        View Feed
                    </button>
                 )}
               </div>
             </Popup>
           </Marker>
         ))}
       </MapContainer>

       {/* Floating Camera List Panel */}
       <div className="absolute top-4 left-4 z-[400] w-72 bg-background/90 backdrop-blur-md rounded-lg border border-primary/30 max-h-[calc(100%-2rem)] flex flex-col shadow-2xl">
          <div className="p-4 border-b border-primary/20">
              <h3 className="font-orbitron text-primary text-xl font-bold flex items-center gap-2">
                 <span className="w-2 h-2 rounded-full bg-alert animate-pulse"/>
                 SYSTEM.MAP
              </h3>
              <p className="text-xs text-text-muted mt-1 font-mono">
                  ACTIVE NODES: {cameras.length}
              </p>
          </div>
          <div className="overflow-y-auto flex-1 p-2 space-y-2 custom-scrollbar">
              {cameras.map(cam => (
                  <div 
                    key={cam.id}
                    onClick={() => setSelectedCamera(cam)}
                    className={`
                        p-3 rounded border cursor-pointer transition-all
                        ${selectedCamera?.id === cam.id 
                            ? 'bg-primary/20 border-primary ml-2' 
                            : 'bg-surface/50 border-transparent hover:border-primary/50 hover:bg-surface/80'}
                    `}
                  >
                      <div className="flex justify-between items-start">
                          <span className="text-sm font-medium truncate w-[130px]">{cam.name}</span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase ${getStatusColor(cam.status)}`}>
                              {cam.status}
                          </span>
                      </div>
                      <div className="text-[10px] text-text-muted mt-1 font-mono">
                          LAT: {cam.location.lat.toFixed(3)} | LNG: {cam.location.lng.toFixed(3)}
                      </div>
                  </div>
              ))}
          </div>
       </div>

       {/* Map Overlay CSS for Dark Mode Tiles */}
       <style jsx global>{`
         .map-tiles-dark {
            filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%);
         }
         .leaflet-popup-content-wrapper {
            background: rgba(15, 23, 42, 0.95);
            color: #e2e8f0;
            border: 1px solid #0ea5e9;
            border-radius: 4px;
         }
         .leaflet-popup-tip {
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid #0ea5e9;
         }
         .leaflet-container {
             font-family: var(--font-inter), sans-serif;
         }
       `}</style>
    </div>
  );
};

export default CityMap;
