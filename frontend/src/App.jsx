import React from "react";
import { LogOut } from "lucide-react";
import { apiRequest } from "./api.js";
import { SOURCES, STATUSES } from "./constants.js";
import Login from "./components/Login.jsx";
import RawRowsTable from "./components/RawRowsTable.jsx";
import RecordDetail from "./components/RecordDetail.jsx";
import RecordsTable from "./components/RecordsTable.jsx";
import Summary from "./components/Summary.jsx";
import UploadPanel from "./components/UploadPanel.jsx";

export default function App() {
  const [token, setToken] = React.useState(localStorage.getItem("token") || "");
  const [summary, setSummary] = React.useState(null);
  const [batches, setBatches] = React.useState([]);
  const [records, setRecords] = React.useState([]);
  const [rawRows, setRawRows] = React.useState([]);
  const [activity, setActivity] = React.useState([]);
  const [activeStatus, setActiveStatus] = React.useState("PENDING");
  const [sourceFilter, setSourceFilter] = React.useState("ALL");
  const [selected, setSelected] = React.useState(null);
  const [notification, setNotification] = React.useState({ text: "", type: "" });
  const [loading, setLoading] = React.useState(false);
  const [selectedBatchToLock, setSelectedBatchToLock] = React.useState("");

  const setMessage = React.useCallback((text, type = "info") => {
    setNotification({ text, type });
  }, []);

  async function lockRecord(recordId) {
    try {
      await api(`/records/${recordId}/lock/`, { method: "POST" });
      setMessage("Record locked successfully.", "success");
      await loadDashboard();
    } catch (error) {
      setMessage(error.message, "error");
    }
  }

  function api(path, options = {}) {
    return apiRequest(path, { token, ...options });
  }

  async function loadActivity(recordId) {
    try {
      const logs = await api(`/records/${recordId}/activity/`);
      setActivity(logs);
    } catch {
      setActivity([]);
    }
  }

  async function loadDashboard() {
    if (!token) return;

    setLoading(true);
    setNotification({ text: "", type: "" });

    try {
      const statusParam = activeStatus !== "FAILED" ? `?status=${activeStatus}` : "";
      const sourceParam =
        sourceFilter !== "ALL" ? `${statusParam ? "&" : "?"}source_type=${sourceFilter}` : "";

      const [nextSummary, nextBatches, nextRecords, nextRawRows] = await Promise.all([
        api("/dashboard/summary/"),
        api("/batches/"),
        activeStatus !== "FAILED" ? api(`/records/${statusParam}${sourceParam}`) : Promise.resolve([]),
        activeStatus === "FAILED" ? api("/raw-rows/?parse_status=FAILED") : Promise.resolve([]),
      ]);

      setSummary(nextSummary || {});
      setBatches(Array.isArray(nextBatches) ? nextBatches : []);
      setRecords(Array.isArray(nextRecords) ? nextRecords : []);
      setRawRows(Array.isArray(nextRawRows) ? nextRawRows : []);

      if (selected?.id) {
        if (Array.isArray(nextRecords) && nextRecords.some(r => r.id === selected.id)) {
          loadActivity(selected.id);
        } else {
          setSelected(null);
        }
      }
    } catch (error) {
      setMessage(error.message, "error");
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => {
    loadDashboard();
  }, [token, activeStatus, sourceFilter]);

  function handleLogout() {
    api("/auth/logout/", { method: "POST" }).catch(() => {});
    localStorage.removeItem("token");
    setToken("");
    setSelected(null);
  }

  if (!token) {
    return <Login setToken={setToken} setMessage={setMessage} message={notification.text} />;
  }

  const filteredRawRows =
    sourceFilter === "ALL" ? rawRows : rawRows.filter((row) => row.source_type === sourceFilter);

  return (
    <div className="appShell">
      <header className="topbar">
        <div>
          <h1>Breathe ESG Review</h1>
          <p>{summary?.client?.name || "Client"} ingestion dashboard</p>
        </div>
        <div className="topActions">
          <button className="iconText" onClick={handleLogout}>
            <LogOut size={16} /> Logout
          </button>
        </div>
      </header>

      {notification.text && (
        <div className={`notice ${notification.type === "error" ? "error" : ""}`}>
          {notification.text}
        </div>
      )}

      <main className="mainGrid">
        <section className="leftPane">
          <Summary summary={summary} />
          <UploadPanel api={api} reload={loadDashboard} setMessage={setMessage} />
        </section>

        <section className="workPane">
          <div className="toolbar">
            <div className="tabs">
              {STATUSES.map((status) => (
                <button
                  key={status}
                  className={activeStatus === status ? "active" : ""}
                  onClick={() => {
                    setActiveStatus(status);
                    setSelected(null);
                  }}
                >
                  {status}
                </button>
              ))}
            </div>
            <select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)}>
              {SOURCES.map((source) => (
                <option key={source} value={source}>
                  {source}
                </option>
              ))}
            </select>
          </div>

          {activeStatus === "FAILED" ? (
            <RawRowsTable rows={filteredRawRows} />
          ) : (
            <RecordsTable
              records={records}
              selected={selected}
              onSelect={(record) => {
                setSelected(record);
                loadActivity(record.id);
              }}
              onLock={lockRecord}
            />
          )}
        </section>

        <aside className="detailPane">
          <RecordDetail
            api={api}
            record={selected}
            activity={activity}
            reload={loadDashboard}
            setSelected={setSelected}
            setMessage={setMessage}
          />
        </aside>
      </main>
    </div>
  );
}
