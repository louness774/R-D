import { useState } from 'react';
import { Upload, AlertTriangle, CheckCircle, FileText, ChevronRight } from 'lucide-react';
import PDFViewer from './components/PDFViewer';
import ErrorBoundary from './components/ErrorBoundary';
import './main.css';

const API_URL = "http://localhost:8000";

function AppContent() {
  const [file, setFile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [error, setError] = useState(null);

  const handleFileUpload = async (e) => {
    const uploadedFile = e.target.files[0];
    if (!uploadedFile) return;

    console.log("File selected:", uploadedFile);
    setFile(uploadedFile);
    setLoading(true);
    setAnalysis(null);
    setSelectedAnomaly(null); // Reset selection
    setError(null);

    const formData = new FormData();
    formData.append("file", uploadedFile);

    try {
      console.log("Sending request to backend...");
      const res = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        body: formData,
      });
      console.log("Response received:", res.status);

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Erreur serveur (${res.status}): ${errorText}`);
      }

      const data = await res.json();
      console.log("Data received:", data);

      setAnalysis(data);
      if (data.anomalies && data.anomalies.length > 0) {
        setSelectedAnomaly(data.anomalies[0]);
      }
    } catch (err) {
      console.error("Analysis failed:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getHighlights = () => {
    if (!selectedAnomaly) return [];
    // Map references to simplified boxes
    return selectedAnomaly.references.map(ref => ({
      page: ref.page,
      bbox: ref.bbox,
      label: selectedAnomaly.title
    }));
  };

  return (
    <div className="main-layout">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="header">
          <h3>Payslip Inspector</h3>
        </div>

        <div className="upload-zone">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            id="file-upload"
            style={{ display: 'none' }}
          />
          <label htmlFor="file-upload">
            <Upload size={32} style={{ marginBottom: 12 }} />
            <p>Glisser un PDF ou cliquer pour importer</p>
          </label>
        </div>

        {loading && <div style={{ padding: 20, textAlign: 'center' }}>Analyse en cours...</div>}

        {error && (
          <div style={{ padding: 15, margin: 10, background: '#fee2e2', color: '#b91c1c', borderRadius: 6, fontSize: '0.9em' }}>
            <strong>Erreur :</strong> {error}
          </div>
        )}

        {analysis && (
          <div className="results-panel">
            <div className={`status-badge ${analysis.status === 'OK' ? 'status-ok' : 'status-error'}`}>
              {analysis.status === 'OK' ? <CheckCircle size={16} /> : <AlertTriangle size={16} />}
              {analysis.status === 'OK' ? "Aucune anomalie détectée" : `${analysis.anomalies.length} anomalie(s) détectée(s)`}
            </div>

            <div className="anomalies-list">
              {analysis.anomalies.map((anomaly, idx) => (
                <div
                  key={idx}
                  className={`anomaly-card ${selectedAnomaly === anomaly ? 'selected' : ''}`}
                  onClick={() => setSelectedAnomaly(anomaly)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, color: '#ef4444' }}>{anomaly.title}</span>
                    <span style={{ fontSize: '0.8em', background: '#fee2e2', padding: '2px 6px', borderRadius: 4 }}>
                      {anomaly.code}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.9em', color: '#4b5563' }}>{anomaly.explanation}</p>
                </div>
              ))}
            </div>

            {/* Extracted Data Preview (Optional) */}
            <div style={{ marginTop: 24 }}>
              <h4>Données extraites</h4>
              <div style={{ fontSize: '0.85em', color: '#64748b' }}>
                <p>Net: {analysis?.extracted_data?.net_a_payer?.value} €</p>
                <p>Brut: {analysis?.extracted_data?.salaire_brut?.value} €</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content (PDF) */}
      <div className="content-area">
        {file ? (
          <PDFViewer
            file={file}
            boxes={getHighlights()}
          />
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#94a3b8' }}>
            <FileText size={64} style={{ opacity: 0.2 }} />
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  );
}
