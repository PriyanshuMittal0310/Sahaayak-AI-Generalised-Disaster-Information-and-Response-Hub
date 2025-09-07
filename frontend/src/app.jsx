import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from 'leaflet';
import "leaflet/dist/leaflet.css";

// Fix for default marker icons in Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png')
});

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
      console.log('Submitting report to:', `${API_URL}/api/ingest`);
      
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
        console.error('Submit error response:', errorText);
        throw new Error(`HTTP error! status: ${res.status} - ${errorText}`);
      }
      
      const out = await res.json();
      console.log('Submit response:', out);
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
    <form onSubmit={submit} style={{ display: "grid", gap: 8, maxWidth: 520 }}>
      <textarea
        placeholder="Describe what you see (flooding, fire, etc.)"
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={4}
        required
      />
      <div style={{ display: "flex", gap: 8 }}>
        <input
          type="number" step="any" placeholder="Lat"
          value={coords.lat} onChange={(e) => setCoords({ ...coords, lat: e.target.value })}
          style={{ flex: 1 }}
        />
        <input
          type="number" step="any" placeholder="Lon"
          value={coords.lon} onChange={(e) => setCoords({ ...coords, lon: e.target.value })}
          style={{ flex: 1 }}
        />
        <button type="button" onClick={useMyLocation}>Use GPS</button>
      </div>
      <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      <button disabled={submitting}>
        {submitting ? "Submitting..." : "Submit report"}
      </button>
    </form>
  );
}

// Helper function to get marker color based on source
const getMarkerColor = (source) => {
  switch(source?.toUpperCase()) {
    case 'USGS':
      return 'red';
    case 'REDDIT':
      return 'blue';
    case 'X':
      return 'black';
    case 'CITIZEN':
      return 'green';
    default:
      return 'gray';
  }
};

export default function App() {
  const [tab, setTab] = useState("map");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [credibilityFilter, setCredibilityFilter] = useState("all");
  const centerIndia = [20.59, 78.96];
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const fetchData = async (retryCount = 0) => {
    const MAX_RETRIES = 3;
    try {
      setLoading(true);
      setError(null);
      
      console.log('Fetching data from:', API_URL);
      
      // Test backend connection first
      const healthRes = await fetch(`${API_URL}/health`);
      if (!healthRes.ok) {
        throw new Error(`Backend not responding: ${healthRes.status}`);
      }
      console.log('Backend health check passed');
      
      // Fetch USGS data
      console.log('Fetching USGS data...');
      const usgsRes = await fetch(`${API_URL}/ingest/usgs`);
      if (!usgsRes.ok) {
        const usgsError = await usgsRes.text();
        console.error('USGS fetch error:', usgsError);
        throw new Error(`Failed to fetch USGS data: ${usgsRes.status}`);
      }
      console.log('USGS data fetched successfully');
      
      // Fetch all items with retry logic
      let itemsRes;
      let itemsData;
      
      try {
        console.log('Fetching items...');
        itemsRes = await fetch(`${API_URL}/api/items`);
        if (!itemsRes.ok) {
          throw new Error(`Failed to fetch items: ${itemsRes.status} ${itemsRes.statusText}`);
        }
        itemsData = await itemsRes.json();
      } catch (fetchError) {
        if (retryCount < MAX_RETRIES) {
          console.log(`Retrying fetch (${retryCount + 1}/${MAX_RETRIES})...`);
          // Wait for 1 second before retrying
          await new Promise(resolve => setTimeout(resolve, 1000));
          return fetchData(retryCount + 1);
        }
        throw fetchError;
      }
      
      if (itemsData && itemsData.items) {
        console.log('Items fetched successfully:', itemsData.count, 'items');
        setItems(itemsData.items);
      } else {
        console.warn('Unexpected API response format:', itemsData);
        setItems([]);
      }
      
    } catch (error) {
      console.error('Error fetching data:', error);
      setError(`Connection failed: ${error.message}. Please ensure the backend is running on ${API_URL}`);
      // Show error in the UI for 5 seconds
      setTimeout(() => setError(null), 5000);
    } finally {
      setLoading(false);
    }
  };

  // Function to refresh data
  const refresh = async () => {
    try {
      setLoading(true);
      await fetchData();
    } catch (error) {
      console.error('Error refreshing data:', error);
      setError('Failed to refresh data');
    } finally {
      setLoading(false);
    }
  };

  // Initial data fetch
  useEffect(() => { fetchData(); }, []);

  // Filter items by source for better organization
  const citizenReports = items.filter(item => item.source === 'CITIZEN');
  
  // Filter items by credibility
  const filteredItems = items.filter(item => {
    if (credibilityFilter === "all") return true;
    if (credibilityFilter === "high" && item.score_credibility >= 0.7) return true;
    if (credibilityFilter === "medium" && item.score_credibility >= 0.4 && item.score_credibility < 0.7) return true;
    if (credibilityFilter === "low" && item.score_credibility < 0.4) return true;
    if (credibilityFilter === "needs_review" && item.needs_review === 'true') return true;
    if (credibilityFilter === "suspected_rumor" && item.suspected_rumor === 'true') return true;
    return false;
  });

  // Format content based on item source
  const formatContent = (item) => {
    const isEarthquake = item.source === 'USGS';
    const isGDACS = item.source === 'GDACS';
    const isCitizen = item.source === 'CITIZEN';
    const isReliefWeb = item.source === 'ReliefWeb';
    const isRSS = ['GDACS', 'ReliefWeb'].includes(item.source) ? false : item.source === 'RSS';
    
    // Parse the raw JSON if it's a string
    let rawData = item.raw_json;
    if (typeof rawData === 'string') {
      try {
        rawData = JSON.parse(rawData);
      } catch (e) {
        console.warn('Failed to parse raw JSON:', e);
        rawData = {};
      }
    }
    
    if (isEarthquake) {
      return (
        <>
          <div style={{ marginBottom: '6px' }}>
            <strong>Magnitude:</strong> {item.magnitude?.toFixed(1) || 'N/A'}
          </div>
          {item.place && (
            <div style={{ marginBottom: '6px' }}>
              <strong>Location:</strong> {item.place}
            </div>
          )}
          {(rawData?.time_utc || rawData?.published) && (
            <div style={{ fontSize: '0.9em', color: '#666', marginBottom: '6px' }}>
              {new Date(rawData.time_utc || rawData.published).toLocaleString()}
            </div>
          )}
          {(rawData?.url || rawData?.link) && (
            <a 
              href={rawData.url || rawData.link} 
              target="_blank" 
              rel="noopener noreferrer"
              style={{ color: '#007bff', textDecoration: 'none' }}
            >
              View on {isEarthquake ? 'USGS' : 'Source'}
            </a>
          )}
        </>
      );
    } else if (isReliefWeb || isRSS) {
      return (
        <>
          <div style={{ marginBottom: '8px' }}>
            {rawData?.summary ? (
              <div dangerouslySetInnerHTML={{ __html: rawData.summary }} />
            ) : (
              <div>{item.text || rawData?.title || 'No description available'}</div>
            )}
          </div>
          {(item.place || rawData?.location) && (
            <div style={{ marginBottom: '6px' }}>
              <strong>Location:</strong> {item.place || rawData?.location}
            </div>
          )}
          {rawData?.published && (
            <div style={{ fontSize: '0.9em', color: '#666', marginBottom: '6px' }}>
              {new Date(rawData.published).toLocaleString()}
            </div>
          )}
          {rawData?.link && (
            <a 
              href={rawData.link} 
              target="_blank" 
              rel="noopener noreferrer"
              style={{ color: '#007bff', textDecoration: 'none' }}
            >
              View on {isReliefWeb ? 'ReliefWeb' : 'Source'}
            </a>
          )}
        </>
      );
    } else if (isGDACS) {
      return (
        <>
          <div style={{ marginBottom: '6px' }}>
            <strong>Alert:</strong> {item.text?.split('|')[0]?.trim()}
          </div>
          {item.place && (
            <div style={{ marginBottom: '6px' }}>
              <strong>Location:</strong> {item.place}
            </div>
          )}
          {item.raw_json?.published && (
            <div style={{ fontSize: '0.9em', color: '#666', marginBottom: '6px' }}>
              {new Date(item.raw_json.published).toLocaleString()}
            </div>
          )}
          {item.raw_json?.link && (
            <a 
              href={item.raw_json.link} 
              target="_blank" 
              rel="noopener noreferrer"
              style={{ color: '#007bff', textDecoration: 'none' }}
            >
              View Details
            </a>
          )}
        </>
      );
    } else if (isCitizen) {
      return (
        <>
          <div style={{ marginBottom: '6px' }}>
            {item.text}
          </div>
          {item.place && (
            <div style={{ marginBottom: '6px' }}>
              <strong>Location:</strong> {item.place}
            </div>
          )}
          {item.media_url && (
            <div style={{ marginTop: '6px' }}>
              <img 
                src={`${API_URL}${item.media_url}`} 
                alt="Report media" 
                style={{ maxWidth: '100%', height: 'auto', borderRadius: '4px' }} 
              />
            </div>
          )}
          <div style={{ fontSize: '0.8em', color: '#666', marginTop: '6px' }}>
            {new Date(item.created_at).toLocaleString()}
          </div>
        </>
      );
    }
    
    // Default content for other sources
    return (
      <div>
        <div style={{ marginBottom: '6px' }}>{item.text}</div>
        {item.media_url && (
          <img 
            src={`${API_URL}${item.media_url}`} 
            alt="" 
            style={{ maxWidth: '100%', height: 'auto', borderRadius: '4px' }} 
          />
        )}
      </div>
    );
  };

  return (
    <div style={{ height: "100vh", width: "100%", display: "grid", gridTemplateRows: "48px 1fr" }}>
      {/* Header */}
      <div style={{ display: "flex", gap: 12, alignItems: "center", padding: "8px 12px", borderBottom: "1px solid #eee" }}>
        <strong style={{ fontSize: '1.2rem' }}>🌍 CrisisConnect</strong>
        <button 
          onClick={() => setTab("map")} 
          style={{
            background: tab === "map" ? '#007bff' : 'transparent',
            color: tab === "map" ? 'white' : 'black',
            border: '1px solid #ddd',
            padding: '4px 12px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: tab === "map" ? 'bold' : 'normal'
          }}
        >
          Map View
        </button>
        <button 
          onClick={() => setTab("report")} 
          style={{
            background: tab === "report" ? '#28a745' : 'transparent',
            color: tab === "report" ? 'white' : 'black',
            border: '1px solid #ddd',
            padding: '4px 12px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: tab === "report" ? 'bold' : 'normal'
          }}
        >
          Report Incident
        </button>
        <select
          value={credibilityFilter}
          onChange={(e) => setCredibilityFilter(e.target.value)}
          style={{
            padding: '6px 12px',
            borderRadius: '4px',
            border: '1px solid #ddd',
            background: 'white',
            fontSize: '0.9em',
            cursor: 'pointer'
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
          onClick={refresh} 
          style={{ 
            marginLeft: "auto",
            background: '#6c757d',
            color: 'white',
            border: 'none',
            padding: '6px 12px',
            borderRadius: '4px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            fontWeight: 'bold',
            fontSize: '0.9em'
          }}
          disabled={loading}
        >
          {loading ? '⟳ Refreshing...' : '⟳ Refresh Data'}
        </button>
      </div>

      {/* Loading Indicator */}
      {loading && (
        <div style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          background: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
          zIndex: 1000
        }}>
          Loading latest data...
        </div>
      )}
      
      {/* Error Message */}
      {error && (
        <div style={{
          position: 'fixed',
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
          gap: '10px'
        }}>
          <span>⚠️ {error}</span>
          <button 
            onClick={refresh}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#721c24',
              cursor: 'pointer',
              textDecoration: 'underline'
            }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Main Content */}
      {tab === "map" ? (
        <div style={{ position: 'relative', height: '100%' }}>
          <MapContainer 
            center={centerIndia} 
            zoom={5}
            minZoom={2}
            style={{ height: "100%", width: "100%" }}
            zoomControl={false}
            worldCopyJump={false}
            maxBounds={[[-85, -180], [85, 180]]}
            maxBoundsViscosity={1.0}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              noWrap={true}
            />
            
            {/* Legend */}
            <div style={{
              position: 'absolute',
              bottom: '20px',
              right: '10px',
              zIndex: 1000,
              background: 'rgba(255, 255, 255, 0.9)',
              padding: '10px',
              borderRadius: '4px',
              boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
              fontSize: '12px',
              backdropFilter: 'blur(2px)'
            }}>
              <div style={{ marginBottom: '5px', fontWeight: 'bold', fontSize: '13px' }}>Map Legend</div>
              {[
                { type: 'Earthquakes', color: 'USGS' },
                { type: 'Alerts', color: 'GDACS' },
                { type: 'Citizen Reports', color: 'CITIZEN' },
                { type: 'ReliefWeb', color: 'ReliefWeb' },
                { type: 'Other Feeds', color: 'RSS' }
              ].map((item, index) => (
                <div key={index} style={{ display: 'flex', alignItems: 'center', marginBottom: '3px' }}>
                  <div style={{
                    width: '12px',
                    height: '12px',
                    background: getMarkerColor(item.color),
                    borderRadius: '50%',
                    marginRight: '6px',
                    border: '1px solid white',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.2)'
                  }}></div>
                  <span>{item.type}</span>
                </div>
              ))}
            </div>

            {/* Map Markers */}
            {filteredItems
              .filter(item => item.lat != null && item.lon != null)
              .map((item) => {
                const color = getMarkerColor(item.source);
                const isEarthquake = item.source === 'USGS';
                const isGDACS = item.source === 'GDACS';
                const isCitizen = item.source === 'CITIZEN';
                
                // Calculate marker size based on magnitude for earthquakes, or use default for others
                const markerSize = isEarthquake && item.magnitude 
                  ? Math.min(30, Math.max(15, item.magnitude * 5)) 
                  : 20;
                
                return (
                  <Marker 
                    key={`${item.source}_${item.id}`} 
                    position={[item.lat, item.lon]}
                    icon={L.divIcon({
                      className: 'custom-marker',
                      html: `
                        <div style="
                          background: ${color};
                          width: ${markerSize}px;
                          height: ${markerSize}px;
                          border-radius: 50%;
                          border: 2px solid white;
                          display: flex;
                          align-items: center;
                          justify-content: center;
                          color: white;
                          font-weight: bold;
                          transform: translate(-50%, -50%);
                          box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                          font-size: ${Math.max(10, markerSize * 0.6)}px;
                        ">
                          ${isEarthquake ? item.magnitude?.toFixed(1) || '?' : ''}
                        </div>
                      `,
                      iconSize: [markerSize, markerSize],
                      iconAnchor: [markerSize / 2, markerSize / 2],
                      popupAnchor: [0, -markerSize / 2]
                    })}
                  >
                    <Popup closeButton={false}>
                      <div style={{ maxWidth: 300, minWidth: 200, padding: '8px' }}>
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: '8px',
                          marginBottom: '12px',
                          paddingBottom: '8px',
                          borderBottom: '1px solid #eee'
                        }}>
                          <div style={{
                            width: '14px',
                            height: '14px',
                            background: color,
                            borderRadius: '50%',
                            flexShrink: 0,
                            border: '1px solid white',
                            boxShadow: '0 1px 3px rgba(0,0,0,0.2)'
                          }}></div>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: '1.1em', fontWeight: 'bold', lineHeight: '1.2' }}>
                              {isEarthquake ? 'Earthquake' : isGDACS ? 'Disaster Alert' : isCitizen ? 'Citizen Report' : 'Report'}
                            </div>
                            <div style={{ fontSize: '0.85em', color: '#666', marginTop: '2px' }}>
                              {item.source}{item.source_handle && ` • ${item.source_handle}`}
                            </div>
                          </div>
                          {/* Credibility Score Display */}
                          {item.score_credibility !== null && item.score_credibility !== undefined && (
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px',
                              fontSize: '0.8em',
                              background: item.score_credibility >= 0.7 ? '#d4edda' : 
                                         item.score_credibility >= 0.4 ? '#fff3cd' : '#f8d7da',
                              color: item.score_credibility >= 0.7 ? '#155724' : 
                                    item.score_credibility >= 0.4 ? '#856404' : '#721c24',
                              padding: '2px 6px',
                              borderRadius: '12px',
                              border: '1px solid',
                              borderColor: item.score_credibility >= 0.7 ? '#c3e6cb' : 
                                         item.score_credibility >= 0.4 ? '#ffeaa7' : '#f5c6cb'
                            }}>
                              <span>🔍</span>
                              <span>{(item.score_credibility * 100).toFixed(0)}%</span>
                            </div>
                          )}
                        </div>
                        {formatContent(item)}
                        
                        {/* Credibility Flags */}
                        {(item.needs_review === 'true' || item.suspected_rumor === 'true') && (
                          <div style={{ 
                            marginTop: '8px', 
                            padding: '6px 8px', 
                            background: '#f8f9fa', 
                            borderRadius: '4px',
                            border: '1px solid #dee2e6',
                            fontSize: '0.8em'
                          }}>
                            {item.needs_review === 'true' && (
                              <div style={{ color: '#856404', marginBottom: '2px' }}>
                                ⚠️ Needs Review
                              </div>
                            )}
                            {item.suspected_rumor === 'true' && (
                              <div style={{ color: '#721c24' }}>
                                🚨 Suspected Rumor
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </Popup>
                  </Marker>
                );
              })}
          </MapContainer>
        </div>
      ) : (
        <div style={{ 
          padding: '20px', 
          maxWidth: '800px', 
          margin: '0 auto',
          width: '100%',
          overflowY: 'auto'
        }}>
          <div style={{
            background: '#f8f9fa',
            borderRadius: '8px',
            padding: '20px',
            marginBottom: '20px',
            border: '1px solid #dee2e6'
          }}>
            <h2 style={{ marginTop: 0, marginBottom: '16px' }}>Report an Incident</h2>
            <ReportForm onSubmitted={refresh} />
          </div>
          
          {/* Recent Reports Section */}
          {citizenReports.length > 0 && (
            <div style={{ marginTop: '30px' }}>
              <h3 style={{ marginBottom: '15px', color: '#2c3e50' }}>Your Recent Reports</h3>
              <div style={{ display: 'grid', gap: '15px', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))' }}>
                {citizenReports.slice(0, 4).map((report, index) => (
                  <div key={index} style={{ 
                    background: 'white', 
                    borderRadius: '6px', 
                    padding: '15px', 
                    boxShadow: '0 2px 5px rgba(0,0,0,0.05)',
                    border: '1px solid #e9ecef'
                  }}>
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      marginBottom: '10px', 
                      fontSize: '0.85em',
                      color: '#6c757d'
                    }}>
                      <span>Report #{citizenReports.length - index}</span>
                      <span>{new Date(report.created_at).toLocaleDateString()}</span>
                    </div>
                    <div style={{ marginBottom: '10px' }}>
                      {report.text?.length > 100 ? `${report.text.substring(0, 100)}...` : report.text}
                    </div>
                    {report.media_url && (
                      <div style={{ marginTop: '10px' }}>
                        <img 
                          src={`${API_URL}${report.media_url}`} 
                          alt="Report media" 
                          style={{ 
                            width: '100%', 
                            height: '120px',
                            objectFit: 'cover',
                            borderRadius: '4px'
                          }} 
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
