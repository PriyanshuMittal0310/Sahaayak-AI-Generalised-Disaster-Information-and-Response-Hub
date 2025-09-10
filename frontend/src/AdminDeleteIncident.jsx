import React, { useState } from 'react';

export default function AdminDeleteIncident({ onDelete }) {
  const [incidentId, setIncidentId] = useState('');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState('');

  const handleDelete = async () => {
    if (password !== 'OpenAI2025!') {
      setStatus('Incorrect admin password.');
      return;
    }
    setStatus('Deleting...');
    try {
      await onDelete(incidentId);
      setStatus('Incident deleted successfully.');
    } catch (err) {
      setStatus('Delete failed: ' + err.message);
    }
  };

  return (
    <div style={{ marginTop: 20 }}>
      <h4>Delete Citizen Report</h4>
      <input
        type="text"
        placeholder="Incident ID"
        value={incidentId}
        onChange={e => setIncidentId(e.target.value)}
        style={{ marginRight: 8 }}
      />
      <input
        type="password"
        placeholder="Admin Password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        style={{ marginRight: 8 }}
      />
      <button onClick={handleDelete} style={{ padding: '6px 12px' }}>Delete</button>
      <div style={{ marginTop: 8, color: '#888' }}>{status}</div>
    </div>
  );
}
