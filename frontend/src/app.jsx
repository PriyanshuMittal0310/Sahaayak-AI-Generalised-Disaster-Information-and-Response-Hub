import { useEffect, useState, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from 'leaflet';
import "leaflet/dist/leaflet.css";
import AdminDeleteIncident from './AdminDeleteIncident';

// Component to handle map view updates
const MapViewManager = ({ bounds }) => {
  const map = useMap();
  const hasSetBounds = useRef(false);

  useEffect(() => {
    if (bounds && !hasSetBounds.current) {
      map.fitBounds(bounds, { padding: [50, 50] });
      hasSetBounds.current = true;
    }
  }, [bounds, map]);

  return null;
};

// Fix for default marker icons in Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png')
});

// Report Form Component
function ReportForm({ onSubmitted }) {
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [coords, setCoords] = useState({ lat: "", lon: "" });
  const [submitting, setSubmitting] = useState(false);
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const useMyLocation = async () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => setCoords({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      (err) => console.error('Error getting location:', err)
    );
  };


  const handleTextChange = (e) => {
    setText(e.target.value);
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    setSubmitting(true);
    try {
      let res;
      if (file) {
        // Use FormData for file upload
        const formData = new FormData();
        formData.append('text', text);
        formData.append('detect_language', 'true');
        formData.append('use_openai', 'true');
        formData.append('lat', coords.lat);
        formData.append('lon', coords.lon);
        formData.append('file', file);
        res = await fetch(`${API_URL}/api/disasters/detect`, {
          method: 'POST',
          body: formData
        });
      } else {
        // Send as JSON if no file
        const payload = {
          text: text,
          detect_language: true,
          use_openai: true,
          lat: coords.lat,
          lon: coords.lon
        };
        res = await fetch(`${API_URL}/api/disasters/detect`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload)
        });
      }
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`HTTP error! status: ${res.status} - ${errorText}`);
      }
      const result = await res.json();
      setSubmitting(false);
      setText("");
      setFile(null);
      setCoords({ lat: "", lon: "" });
      onSubmitted?.(result);
      if (result.disaster_type) {
        alert(`Report submitted successfully! Detected disaster: ${result.disaster_type}`);
      } else {
        alert("Report submitted successfully!");
      }
    } catch (error) {
      console.error('Error submitting report:', error);
      alert(`Error: ${error.message}`);
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={submit} style={{ display: "grid", gap: 8, maxWidth: 520, padding: '20px' }}>
      <h3>Report an Incident</h3>
      <label>Report Details (required)</label>
      <textarea 
        placeholder="Describe what you see (flooding, fire, etc.)"
        value={text}
        onChange={handleTextChange}
        rows={4}
        required
        style={{ width: '100%' }}
      />
      <div style={{ display: "flex", gap: 8 }}>
        <input
          type="number" step="any" placeholder="Latitude"
          value={coords.lat} onChange={(e) => setCoords({ ...coords, lat: e.target.value })}
          style={{ flex: 1, padding: '8px' }}
        />
        <input
          type="number" step="any" placeholder="Longitude"
          value={coords.lon} onChange={(e) => setCoords({ ...coords, lon: e.target.value })}
          style={{ flex: 1, padding: '8px' }}
        />
        <button 
          type="button" 
          onClick={useMyLocation}
          style={{ padding: '8px 12px', cursor: 'pointer' }}
        >
          Use GPS
        </button>
      </div>
      <input 
        type="file" 
        accept="image/*" 
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        style={{ margin: '8px 0' }}
      />
      <button 
        type="submit"
        disabled={submitting}
        style={{
          padding: '10px',
          background: submitting ? '#ccc' : '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: submitting ? 'not-allowed' : 'pointer'
        }}
      >
        {submitting ? "Submitting..." : "Submit Report"}
      </button>
    </form>
  );
}

// Helper function to get marker icon based on disaster type and source
const getMarkerIcon = (disasterType, source) => {
  // Default to source-based color if no disaster type
  const type = disasterType?.toLowerCase() || '';
  
  // Define colors and icons for different disaster types
  const disasterTypes = {
    // Earthquakes
    earthquake: { color: '#ff0000', icon: '🌋' },
    
    // Floods
    flood: { color: '#1e90ff', icon: '🌊' },
    
    // Storms
    storm: { color: '#4682b4', icon: '🌪️' },
    cyclone: { color: '#4682b4', icon: '🌀' },
    hurricane: { color: '#4682b4', icon: '🌀' },
    typhoon: { color: '#4682b4', icon: '🌀' },
    
    // Droughts
    drought: { color: '#ff8c00', icon: '🏜️' },
    
    // Wildfires
    wildfire: { color: '#ff4500', icon: '🔥' },
    fire: { color: '#ff4500', icon: '🔥' },
    
    // Volcanoes
    volcano: { color: '#8b0000', icon: '🌋' },
    
    // Tsunamis
    tsunami: { color: '#0000ff', icon: '🌊' },
    
    // Default for other disaster types
    default: { 
      color: '#555555', 
      icon: '⚠️',
      // Source-based fallback colors
      sourceColors: {
        'USGS': '#ff0000',
        'GDACS': '#32cd32',
        'REDDIT': '#1da1f2',
        'X': '#000000',
        'CITIZEN': '#9370db'
      }
    }
  };

  // Find the disaster type or use default
  const disaster = Object.entries(disasterTypes).find(([key]) => 
    key === type || type.includes(key)
  )?.[1] || disasterTypes.default;

  // Create HTML for the marker
  const html = `
    <div style="
      background: ${disaster.color || disaster.sourceColors?.[source] || '#555555'};
      width: 28px;
      height: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      border: 2px solid white;
      box-shadow: 0 0 4px rgba(0,0,0,0.5);
      color: white;
      font-size: 16px;
      transform: translate(-14px, -14px);
    ">
      ${disaster.icon || '📍'}
    </div>
  `;

  return L.divIcon({
    html,
    className: 'custom-marker',
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14]
  });
};

// Main App Component
export default function App() {
  const [tab, setTab] = useState("map");
  const [alertPreview, setAlertPreview] = useState("");
  const [alertStatus, setAlertStatus] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [credibilityFilter, setCredibilityFilter] = useState("all");
  const [mapKey, setMapKey] = useState(Date.now());
  const mapRef = useRef(null);
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  
  // World bounds for the map view
  const worldBounds = [
    [-90, -180], // Southwest corner
    [90, 180]    // Northeast corner
  ];

  // Filter items based on credibility filter
  const filteredItems = items.filter(item => {
    if (credibilityFilter === "all") return true;
    if (credibilityFilter === "high" && item.score_credibility >= 0.7) return true;
    if (credibilityFilter === "medium" && item.score_credibility >= 0.4 && item.score_credibility < 0.7) return true;
    if (credibilityFilter === "low" && item.score_credibility < 0.4) return true;
    if (credibilityFilter === "needs_review" && item.needs_review === 'true') return true;
    if (credibilityFilter === "suspected_rumor" && item.suspected_rumor === 'true') return true;
    return false;
  });

  // Fetch data function that can be reused
  const fetchData = async () => {
    setLoading(true);
    try {
      // Add timestamp to prevent caching
      const timestamp = Date.now();
      const response = await fetch(`${API_URL}/api/items?t=${timestamp}`);
      const data = await response.json();
      setItems(data.items || []);
      setError(null);
      
      // Force map to re-render with new data
      setMapKey(timestamp);
      
      // If we have a map instance, fit it to show all markers
      if (mapRef.current) {
        const map = mapRef.current;
        const markers = [];
        
        // Collect all marker positions
        (data.items || []).forEach(item => {
          if (item.lat != null && item.lon != null) {
            markers.push([item.lat, item.lon]);
          }
        });
        
        // If we have markers, fit the map to show them
        if (markers.length > 0) {
          const bounds = L.latLngBounds(markers);
          map.fitBounds(bounds, { padding: [50, 50] });
        } else {
          // Default to world view if no markers
          map.fitBounds([[-60, -180], [90, 180]], { padding: [50, 50] });
        }
      }
    } catch (err) {
      console.error('Error fetching items:', err);
      setError('Failed to load data. Please try refreshing.');
    } finally {
      setLoading(false);
    }
  };

  // Initial data fetch on component mount
  useEffect(() => {
    fetchData();
  }, [API_URL]);

  // Handle report submission and refresh
  const handleReportSubmitted = () => {
    fetchData();
  };

  // Clean up map reference on unmount
  useEffect(() => {
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Popup content for each marker
  const popupContent = (item) => {
    const sourceDisplay = item.source === 'CITIZEN' ? 'Citizen Report' : item.source;
    const languageName = item.language || 'Unknown';
    
    return (
      <div style={{ maxWidth: 300, maxHeight: 400, overflow: 'auto' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '10px',
          paddingBottom: '5px',
          borderBottom: '1px solid #eee'
        }}>
          <div style={{ fontWeight: 'bold', fontSize: '16px' }}>
            {item.disaster_type || 'Incident'}
          </div>
          <div style={{
            fontSize: '12px',
            backgroundColor: '#f0f0f0',
            padding: '2px 6px',
            borderRadius: '10px',
            color: '#555'
          }}>
            {sourceDisplay}
          </div>
        </div>
        
        {item.language && (
          <div style={{ 
            fontSize: '12px',
            color: '#666',
            marginBottom: '8px',
            fontStyle: 'italic'
          }}>
            <i className="fas fa-language" style={{ marginRight: '5px' }}></i>
            {languageName}
          </div>
        )}
        
        <div style={{ 
          marginBottom: '10px',
          lineHeight: '1.4',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word'
        }}>
          {item.text}
        </div>
        
        {item.place && (
          <div style={{ 
            marginBottom: '5px', 
            color: '#666',
            fontSize: '13px'
          }}>
            <i className="fas fa-map-marker-alt" style={{ marginRight: '5px' }}></i>
            {item.place}
          </div>
        )}
        
        {item.magnitude && (
          <div style={{ 
            marginBottom: '8px',
            fontSize: '13px'
          }}>
            <i className="fas fa-chart-line" style={{ marginRight: '5px' }}></i>
            <strong>Magnitude:</strong> {item.magnitude}
          </div>
        )}
        
        {item.created_at && (
          <div style={{ 
            fontSize: '11px', 
            color: '#888', 
            marginBottom: '5px',
            marginTop: '10px',
            paddingTop: '5px',
            borderTop: '1px solid #eee'
          }}>
            <i className="far fa-clock" style={{ marginRight: '5px' }}></i>
            {new Date(item.created_at).toLocaleString()}
          </div>
        )}
        
        {item.media_url && (
          <div style={{ 
            marginTop: '10px',
            borderTop: '1px solid #eee',
            paddingTop: '10px'
          }}>
            <img 
              src={`${API_URL}${item.media_url}`} 
              alt="Report media" 
              style={{ 
                maxWidth: '100%', 
                maxHeight: '150px', 
                borderRadius: '4px',
                display: 'block',
                margin: '0 auto'
              }} 
            />
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Header */}
      <div style={{ 
        background: '#f8f9fa', 
        padding: '10px 20px', 
        borderBottom: '1px solid #dee2e6',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '10px',
        zIndex: 1001
      }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem', whiteSpace: 'nowrap' }}>🌍 Disaster Response Map</h1>
        <div style={{ 
          display: 'flex', 
          gap: '10px',
          flexWrap: 'wrap',
          justifyContent: 'flex-end'
        }}>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={() => setTab('map')} style={{ padding: '8px 16px', background: tab === 'map' ? '#007bff' : '#fff', color: tab === 'map' ? '#fff' : '#000', border: '1px solid #dee2e6', borderRadius: '4px', cursor: 'pointer', whiteSpace: 'nowrap' }}>Map View</button>
            <button onClick={() => setTab('report')} style={{ padding: '8px 16px', background: tab === 'report' ? '#28a745' : '#fff', color: tab === 'report' ? '#fff' : '#000', border: '1px solid #dee2e6', borderRadius: '4px', cursor: 'pointer', whiteSpace: 'nowrap' }}>Report Incident</button>
            <button onClick={() => setTab('events')} style={{ padding: '8px 16px', background: tab === 'events' ? '#ffc107' : '#fff', color: tab === 'events' ? '#fff' : '#000', border: '1px solid #dee2e6', borderRadius: '4px', cursor: 'pointer', whiteSpace: 'nowrap' }}>Events</button>
            <button onClick={() => setTab('alerts')} style={{ padding: '8px 16px', background: tab === 'alerts' ? '#17a2b8' : '#fff', color: tab === 'alerts' ? '#fff' : '#000', border: '1px solid #dee2e6', borderRadius: '4px', cursor: 'pointer', whiteSpace: 'nowrap' }}>Alerts</button>
            <button onClick={() => setTab('admin')} style={{ padding: '8px 16px', background: tab === 'admin' ? '#6f42c1' : '#fff', color: tab === 'admin' ? '#fff' : '#000', border: '1px solid #dee2e6', borderRadius: '4px', cursor: 'pointer', whiteSpace: 'nowrap' }}>Admin</button>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <select value={credibilityFilter} onChange={(e) => setCredibilityFilter(e.target.value)} style={{ padding: '8px', borderRadius: '4px', border: '1px solid #dee2e6', cursor: 'pointer', minWidth: '180px' }}>
              <option value="all">All Reports</option>
              <option value="high">High Credibility (70%+)</option>
              <option value="medium">Medium Credibility (40-70%)</option>
              <option value="low">Low Credibility (&lt;40%)</option>
              <option value="needs_review">Needs Review</option>
              <option value="suspected_rumor">Suspected Rumors</option>
            </select>
            <button onClick={fetchData} disabled={loading} style={{ padding: '8px 16px', background: '#6c757d', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', whiteSpace: 'nowrap' }}>{loading ? 'Refreshing...' : '⟳ Refresh Data'}</button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, position: 'relative' }}>
        {tab === 'map' && (
          // ...existing map code...
          <div key={`map-container-${mapKey}`} style={{ height: '100%', width: '100%' }}>
            {/* ...existing MapContainer code... */}
            <MapContainer 
              center={[20, 0]}
              zoom={2}
              minZoom={2}
              maxBounds={worldBounds}
              maxBoundsViscosity={1.0}
              style={{ height: '100%', width: '100%' }}
              whenCreated={(map) => {
                mapRef.current = map;
                map.fitBounds(worldBounds, { padding: [50, 50] });
              }}
            >
              <MapViewManager bounds={worldBounds} />
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' />
              {/* ...existing marker and legend code... */}
              {filteredItems.filter(item => item.lat != null && item.lon != null).map((item) => {
                const disasterType = item.disaster_type?.toLowerCase() || '';
                const source = item.source?.toUpperCase();
                return (
                  <Marker key={`${item.id}-${source}`} position={[item.lat, item.lon]} icon={getMarkerIcon(disasterType, source)} eventHandlers={{ mouseover: (e) => { e.target.openPopup(); } }}>
                    <Popup closeButton={false}>{popupContent(item)}</Popup>
                  </Marker>
                );
              })}
              {/* ...legend code... */}
            </MapContainer>
          </div>
        )}
        {tab === 'report' && (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'flex-start', padding: '20px', overflowY: 'auto', height: '100%', boxSizing: 'border-box' }}>
            <ReportForm onSubmitted={handleReportSubmitted} />
          </div>
        )}
        {tab === 'events' && (
          <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
            <h3>Event Drawer</h3>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {filteredItems.map(item => (
                <li key={item.id} style={{ marginBottom: '16px', borderBottom: '1px solid #eee', paddingBottom: '8px' }}>
                  <strong>{item.disaster_type || 'Incident'}</strong> (Score: {item.score_credibility})<br />
                  <span>{item.text}</span>
                  {item.place && <div style={{ color: '#666', fontSize: '13px' }}>Location: {item.place}</div>}
                  {item.created_at && <div style={{ fontSize: '11px', color: '#888' }}>Reported: {new Date(item.created_at).toLocaleString()}</div>}
                </li>
              ))}
            </ul>
          </div>
        )}
        {tab === 'alerts' && (
          <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
            <h3>Alert Preview & Send</h3>
            <textarea value={alertPreview} onChange={e => setAlertPreview(e.target.value)} placeholder="Type or generate alert message here..." rows={4} style={{ width: '100%' }} />
            <button style={{ marginTop: '10px', padding: '10px 20px', background: '#17a2b8', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }} onClick={async () => {
              setAlertStatus('Sending...');
              try {
                // Call backend to send alert to Telegram
                const res = await fetch(`${API_URL}/api/telegram/send_alert`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ message: alertPreview })
                });
                if (!res.ok) throw new Error('Failed to send alert');
                setAlertStatus('Alert sent to Telegram!');
              } catch (err) {
                setAlertStatus('Send failed: ' + err.message);
              }
            }}>Send Test Alert</button>
            <div style={{ marginTop: '10px', color: '#888' }}>{alertStatus}</div>
          </div>
        )}
        {tab === 'admin' && (
          <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
            {/* AdminDeleteIncident component assumed to exist */}
            <h3>Admin Panel</h3>
            <AdminDeleteIncident onDelete={id => {/* ...existing delete logic... */}} />
          </div>
        )}
        {/* Loading Overlay */}
        {loading && (
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(255, 255, 255, 0.7)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
            <div style={{ background: 'white', padding: '20px 40px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>Loading data...</div>
          </div>
        )}
        {/* Error Message */}
        {error && (
          <div style={{ position: 'absolute', top: '10px', left: '50%', transform: 'translateX(-50%)', background: '#f8d7da', color: '#721c24', padding: '10px 20px', borderRadius: '4px', zIndex: 1000, display: 'flex', alignItems: 'center', gap: '10px', maxWidth: '80%', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
            <span>⚠️ {error}</span>
            <button onClick={() => setError(null)} style={{ background: 'transparent', border: 'none', color: '#721c24', cursor: 'pointer', fontSize: '16px', padding: '0 5px' }}>×</button>
          </div>
        )}
      </div>
    </div>
  );
}
