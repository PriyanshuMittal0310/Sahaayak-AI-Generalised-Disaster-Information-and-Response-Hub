import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix for default marker icons in React Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Function to get marker color based on magnitude
const getMarkerColor = (magnitude) => {
  if (magnitude >= 6) return '#ff0000'; // Red for major earthquakes
  if (magnitude >= 5) return '#ff6600';  // Orange for strong earthquakes
  if (magnitude >= 4) return '#ffcc00';  // Yellow for moderate earthquakes
  return '#00cc00';                      // Green for minor earthquakes
};

// Function to get marker size based on magnitude
const getMarkerSize = (magnitude) => {
  return Math.min(30, Math.max(10, magnitude * 3));
};

// Custom marker icon
const createCustomIcon = (magnitude) => {
  const size = getMarkerSize(magnitude);
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="width: ${size}px; height: ${size}px; 
                    background-color: ${getMarkerColor(magnitude)}; 
                    border-radius: 50%; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    color: white; 
                    font-weight: bold;
                    transform: translate(-50%, -50%);">
              ${magnitude.toFixed(1)}
           </div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
};

export default function App() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const defaultCenter = [20.59, 78.96]; // Center: India
  const zoomLevel = 5;

  const fetchEarthquakes = async () => {
    try {
      const response = await fetch("http://localhost:8000/realtime/earthquakes");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setEvents(data.events || []);
      setError(null);
    } catch (err) {
      console.error("Error fetching earthquake data:", err);
      setError("Failed to load earthquake data. Please try again later.");
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchEarthquakes();

    // Set up auto-refresh every 1 minute
    const intervalId = setInterval(fetchEarthquakes, 60000);

    // Clean up interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  return (
    <div style={{ height: "100vh", width: "100%", position: "relative" }}>
      <div style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        zIndex: 1000,
        background: 'white',
        padding: '10px',
        borderRadius: '4px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
      }}>
        <h2 style={{ margin: '0 0 10px 0' }}>🌍 Real-time Earthquakes</h2>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ width: '12px', height: '12px', backgroundColor: '#00cc00', borderRadius: '50%', marginRight: '5px' }}></div>
            <span>Minor (&lt;4)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ width: '12px', height: '12px', backgroundColor: '#ffcc00', borderRadius: '50%', marginRight: '5px' }}></div>
            <span>Moderate (4-5)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ width: '12px', height: '12px', backgroundColor: '#ff6600', borderRadius: '50%', marginRight: '5px' }}></div>
            <span>Strong (5-6)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ width: '12px', height: '12px', backgroundColor: '#ff0000', borderRadius: '50%', marginRight: '5px' }}></div>
            <span>Major (6+)</span>
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          zIndex: 1000,
          background: 'white',
          padding: '20px',
          borderRadius: '4px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
        }}>
          Loading earthquake data...
        </div>
      ) : error ? (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          zIndex: 1000,
          background: '#ffebee',
          color: '#c62828',
          padding: '20px',
          borderRadius: '4px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
        }}>
          {error}
        </div>
      ) : (
        <MapContainer 
          center={defaultCenter} 
          zoom={zoomLevel} 
          style={{ height: "100%", width: "100%" }}
          zoomControl={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {events.map((event) => {
            if (!event.coordinates || !Array.isArray(event.coordinates) || event.coordinates.length < 2) {
              return null;
            }
            
            const [longitude, latitude] = event.coordinates;
            const magnitude = parseFloat(event.magnitude) || 0;
            
            return (
              <Marker 
                key={event.id} 
                position={[latitude, longitude]}
                icon={createCustomIcon(magnitude)}
              >
                <Popup>
                  <div style={{ minWidth: '200px' }}>
                    <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>{event.place || 'Unknown location'}</h3>
                    <div style={{ marginBottom: '4px' }}>
                      <strong>Magnitude:</strong> {magnitude.toFixed(1)}
                    </div>
                    <div style={{ marginBottom: '4px' }}>
                      <strong>Time (UTC):</strong> {event.time_utc || 'N/A'}
                    </div>
                    {event.depth && (
                      <div style={{ marginBottom: '4px' }}>
                        <strong>Depth:</strong> {Math.round(event.depth)} km
                      </div>
                    )}
                    {event.url && (
                      <div style={{ marginTop: '8px' }}>
                        <a 
                          href={event.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          style={{ color: '#1a73e8', textDecoration: 'none' }}
                        >
                          View on USGS
                        </a>
                      </div>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      )}
    </div>
  );
}
