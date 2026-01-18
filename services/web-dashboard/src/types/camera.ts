export type CameraStatus = 'online' | 'offline' | 'alert';

export interface Camera {
  id: string;
  name: string;
  location: {
    lat: number;
    lng: number;
  };
  status: CameraStatus;
  streamUrl?: string;
  lastUpdate?: string;
  thumbnailUrl?: string;
}
