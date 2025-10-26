/**
 * Simple Test Map - Minimal Leaflet setup to verify it works
 */

import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const TestMap = () => {
  const center = [21.3099, -157.8581]; // Honolulu

  return (
    <div style={{ height: '600px', width: '100%', border: '2px solid red' }}>
      <h3>Test Map - If you see a map with a red circle, Leaflet works!</h3>
      <div style={{ height: '500px', width: '100%' }}>
        <MapContainer
          center={center}
          zoom={10}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <CircleMarker
            center={center}
            radius={20}
            fillColor="red"
            color="red"
            weight={3}
            opacity={1}
            fillOpacity={0.6}
          >
            <Popup>
              <strong>Honolulu, Hawaii</strong><br />
              If you see this, the map is working!
            </Popup>
          </CircleMarker>
        </MapContainer>
      </div>
    </div>
  );
};

export default TestMap;
