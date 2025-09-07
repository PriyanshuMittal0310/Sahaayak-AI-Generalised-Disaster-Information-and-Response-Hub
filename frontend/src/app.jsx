import { useEffect, useState, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from 'leaflet';
import "leaflet/dist/leaflet.css";

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

  const submit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    
    setSubmitting(true);
    try {
      const fd = new FormData();
      fd.append("text", text);
      if (coords.lat && coords.lon) {
        fd.append("lat", coords.lat);
        fd.append("lon", coords.lon);
      }
      if (file) fd.append("file", file);
      
      const res = await fetch(`${API_URL}/api/ingest`, { 
        method: "POST",
        body: fd 
      });
      
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`HTTP error! status: ${res.status} - ${errorText}`);
      }
      
      const out = await res.json();
      setSubmitting(false);
      
      if (out.ok) {
        setText(""); 
        setFile(null); 
        setCoords({ lat: "", lon: "" });
        onSubmitted?.();
        alert("Report submitted successfully!");
      } else {
        alert(out.error || "Failed to submit report");
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
      <textarea
        placeholder="Describe what you see (flooding, fire, etc.)"
        value={text}
        onChange={(e) => setText(e.target.value)}
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
            <button 
              onClick={() => setTab('map')} 
              style={{
                padding: '8px 16px',
                background: tab === 'map' ? '#007bff' : '#fff',
                color: tab === 'map' ? '#fff' : '#000',
                border: '1px solid #dee2e6',
                borderRadius: '4px',
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              Map View
            </button>
            <button 
              onClick={() => setTab('report')}
              style={{
                padding: '8px 16px',
                background: tab === 'report' ? '#28a745' : '#fff',
                color: tab === 'report' ? '#fff' : '#000',
                border: '1px solid #dee2e6',
                borderRadius: '4px',
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              Report Incident
            </button>
          </div>
          
          <div style={{ display: 'flex', gap: '10px' }}>
            <select
              value={credibilityFilter}
              onChange={(e) => setCredibilityFilter(e.target.value)}
              style={{
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid #dee2e6',
                cursor: 'pointer',
                minWidth: '180px'
              }}
            >
              <option value="all">All Reports</option>
              <option value="high">High Credibility (70%+)</option>
              <option value="medium">Medium Credibility (40-70%)</option>
              <option value="low">Low Credibility (&lt;40%)</option>
              <option value="needs_review">Needs Review</option>
              <option value="suspected_rumor">Suspected Rumors</option>
            </select>
            
            <button 
              onClick={fetchData}
              disabled={loading}
              style={{
                padding: '8px 16px',
                background: '#6c757d',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                whiteSpace: 'nowrap'
              }}
            >
              {loading ? 'Refreshing...' : '⟳ Refresh Data'}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, position: 'relative' }}>
        {tab === 'map' ? (
          <div key={`map-container-${mapKey}`} style={{ height: '100%', width: '100%' }}>
            <MapContainer 
              center={[20, 0]}
              zoom={2}
              minZoom={2}
              maxBounds={worldBounds}
              maxBoundsViscosity={1.0}
              style={{ height: '100%', width: '100%' }}
              whenCreated={(map) => {
                mapRef.current = map;
                // Initial fit to world bounds
                map.fitBounds(worldBounds, { padding: [50, 50] });
              }}
            >
              <MapViewManager bounds={worldBounds} />
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              
              {/* Map Markers */}
              {filteredItems
                .filter(item => item.lat != null && item.lon != null)
                .map((item) => {
                  const disasterType = item.disaster_type?.toLowerCase() || '';
                  const source = item.source?.toUpperCase();
                  
                  return (
                    <Marker 
                      key={`${item.id}-${source}`}
                      position={[item.lat, item.lon]}
                      icon={getMarkerIcon(disasterType, source)}
                      eventHandlers={{
                        mouseover: (e) => {
                          e.target.openPopup();
                        }
                      }}
                    >
                      <Popup closeButton={false}>
                        <div style={{ maxWidth: '250px' }}>
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            marginBottom: '8px',
                            paddingBottom: '4px',
                            borderBottom: '1px solid #eee'
                          }}>
                            <span style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              width: '24px',
                              height: '24px',
                              borderRadius: '50%',
                              backgroundColor: '#f0f0f0',
                              marginRight: '8px',
                              fontSize: '16px'
                            }}>
                              {(() => {
                                try {
                                  const iconHtml = getMarkerIcon(disasterType, source).options.html;
                                  const match = iconHtml.match(/>(.*?)<\/div>/);
                                  return match ? match[1] : '📍';
                                } catch (e) {
                                  return '📍';
                                }
                              })()}
                            </span>
                            <strong style={{ flex: 1 }}>
                              {item.disaster_type || 'Incident'}
                              {source && ` (${source})`}
                            </strong>
                            {item.score_credibility !== undefined && (
                              <span style={{
                                padding: '2px 6px',
                                borderRadius: '10px',
                                fontSize: '12px',
                                backgroundColor: item.score_credibility >= 0.7 ? '#d4edda' : 
                                              item.score_credibility >= 0.4 ? '#fff3cd' : '#f8d7da',
                                color: item.score_credibility >= 0.7 ? '#155724' : 
                                     item.score_credibility >= 0.4 ? '#856404' : '#721c24'
                              }}>
                                {Math.round(item.score_credibility * 100)}%
                              </span>
                            )}
                          </div>
                          
                          <div style={{ margin: '8px 0' }}>
                            {item.text || 'No description available'}
                          </div>
                          
                          {item.location_name && (
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              fontSize: '12px',
                              color: '#666',
                              marginBottom: '8px'
                            }}>
                              📍 {item.location_name}
                            </div>
                          )}
                          
                          <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            marginTop: '8px',
                            paddingTop: '4px',
                            borderTop: '1px solid #eee',
                            fontSize: '12px',
                            color: '#666'
                          }}>
                            <span>
                              {item.magnitude && `Magnitude: ${item.magnitude} `}
                            </span>
                            <span>
                              {new Date(item.created_at).toLocaleString()}
                            </span>
                          </div>
                          
                          {item.media_url && (
                            <div style={{ marginTop: '8px' }}>
                              <img 
                                src={item.media_url} 
                                alt="Disaster media" 
                                style={{ 
                                  maxWidth: '100%', 
                                  maxHeight: '150px',
                                  borderRadius: '4px',
                                  marginTop: '8px'
                                }} 
                              />
                            </div>
                          )}
                        </div>
                      </Popup>
                    </Marker>
                  );
                })}
                
                {/* Legend */}
                <div style={{
                  position: 'absolute',
                  bottom: '20px',
                  right: '10px',
                  zIndex: 1000,
                  background: 'rgba(255, 255, 255, 0.9)',
                  padding: '10px',
                  borderRadius: '4px',
                  boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
                  fontSize: '12px'
                }}>
                  <div style={{ marginBottom: '5px', fontWeight: 'bold' }}>Legend</div>
                  {[
                    { label: 'Earthquakes', type: 'earthquake' },
                    { label: 'Floods', type: 'flood' },
                    { label: 'Storms', type: 'storm' },
                    { label: 'Droughts', type: 'drought' },
                    { label: 'Wildfires', type: 'wildfire' },
                    { label: 'Volcanoes', type: 'volcano' },
                    { label: 'Tsunamis', type: 'tsunami' }
                  ].map((item, index) => {
                    let bgColor = '#555';
                    try {
                      const icon = getMarkerIcon(item.type, '');
                      const match = icon.options.html.match(/background: ([^;]+)/);
                      if (match && match[1]) {
                        bgColor = match[1];
                      }
                    } catch (e) {
                      console.warn(`Could not get color for ${item.type}`, e);
                    }
                    
                    return (
                      <div key={index} style={{ display: 'flex', alignItems: 'center', marginBottom: '3px' }}>
                        <div style={{
                          width: '12px',
                          height: '12px',
                          background: bgColor,
                          borderRadius: '50%',
                          marginRight: '6px',
                          flexShrink: 0
                        }}></div>
                        <span>{item.label}</span>
                      </div>
                    );
                  })}
                </div>
            </MapContainer>
          </div>
        ) : (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'flex-start',
            padding: '20px',
            overflowY: 'auto',
            height: '100%',
            boxSizing: 'border-box'
          }}>
            <ReportForm onSubmitted={handleReportSubmitted} />
          </div>
        )}
        
        {/* Loading Overlay */}
        {loading && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(255, 255, 255, 0.7)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000
          }}>
            <div style={{
              background: 'white',
              padding: '20px 40px',
              borderRadius: '8px',
              boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
            }}>
              Loading data...
            </div>
          </div>
        )}
        
        {/* Error Message */}
        {error && (
          <div style={{
            position: 'absolute',
            top: '10px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: '#f8d7da',
            color: '#721c24',
            padding: '10px 20px',
            borderRadius: '4px',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            maxWidth: '80%',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
          }}>
            <span>⚠️ {error}</span>
            <button 
              onClick={() => setError(null)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#721c24',
                cursor: 'pointer',
                fontSize: '16px',
                padding: '0 5px'
              }}
            >
              ×
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
