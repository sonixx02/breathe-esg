import React from "react";
import { Database, Trash2 } from "lucide-react";

export default function UploadPanel({ api, reload, setMessage }) {
  const [busy, setBusy] = React.useState(false);

  async function loadDemo(source) {
    setBusy(true);
    try {
      await api("/demo/load/", { method: "POST", body: { source_type: source } });
      setMessage(`Loaded ${source} demo data.`);
      await reload();
    } catch (error) {
      setMessage(error.message, "error");
    } finally {
      setBusy(false);
    }
  }

  async function clearDemo() {
    if (!window.confirm("Are you sure you want to clear all ingested batches, records, and activity logs?")) return;
    setBusy(true);
    try {
      await api("/demo/clear/", { method: "POST" });
      setMessage("Cleared all ingested batches and records.");
      await reload();
    } catch (error) {
      setMessage(error.message, "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <h2>Load Sample Data</h2>
      <p style={{fontSize: 12, color: '#888', margin: '0 0 12px 0'}}>
        Load realistic sample datasets to explore the review workflow.
      </p>
      <div style={{display: 'flex', gap: '8px', flexWrap: 'wrap'}}>
        {["SAP", "UTILITY", "TRAVEL"].map((source) => (
          <button
            key={source}
            className="iconText"
            onClick={() => loadDemo(source)}
            disabled={busy}
          >
            <Database size={14} /> Load {source}
          </button>
        ))}
      </div>
      <div style={{display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '12px', borderTop: '1px solid #eef2f0', paddingTop: '12px'}}>
        <button
          className="iconText"
          onClick={clearDemo}
          disabled={busy}
          style={{backgroundColor: '#fff', border: '1px solid #ff4d4f', color: '#ff4d4f'}}
        >
          <Trash2 size={14} /> Reset Database
        </button>
      </div>
    </section>
  );
}

