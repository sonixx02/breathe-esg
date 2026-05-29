import React from "react";
import { AlertTriangle, CheckCircle2, FileText } from "lucide-react";
import StatusBadge from "./StatusBadge.jsx";

export default function RecordDetail({ api, record, activity, reload, setSelected, setMessage }) {
  const [form, setForm] = React.useState({});

  React.useEffect(() => {
    setForm(record || {});
  }, [record]);

  if (!record) {
    return (
      <section className="panel detailEmpty">
        <FileText size={24} />
        <p>Select a normalized record to inspect raw source data and review actions.</p>
      </section>
    );
  }

  async function save() {
    try {
      const updated = await api(`/records/${record.id}/`, {
        method: "PATCH",
        body: {
          activity_category: form.activity_category,
          normalized_value: form.normalized_value,
          normalized_unit: form.normalized_unit,
          location_name: form.location_name,
          review_comment: form.review_comment,
        },
      });
      setSelected(updated);
      setMessage("Record saved.");
      await reload();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function approve() {
    try {
      const updated = await api(`/records/${record.id}/approve/`, {
        method: "POST",
        body: { review_comment: form.review_comment || "" },
      });
      setSelected(updated);
      setMessage("Record approved.");
      await reload();
    } catch (error) {
      setMessage(error.message);
    }
  }

  const locked = record.status === "LOCKED";

  return (
    <section className="panel detailPanel">
      <div className="detailTitle">
        <div>
          <h2>Record #{record.id}</h2>
          <p>
            {record.source_type} - Scope {record.scope}
          </p>
        </div>
        <StatusBadge status={record.status} />
      </div>

      {record.flag_reason && (
        <div className="flagBox">
          <AlertTriangle size={16} /> {record.flag_reason}
        </div>
      )}

      <label>
        Category
        <input
          value={form.activity_category || ""}
          disabled={locked}
          onChange={(event) => setForm({ ...form, activity_category: event.target.value })}
        />
      </label>
      <label>
        Raw value (from source)
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <input
            value={`${record.raw_value} ${record.raw_unit}`}
            disabled
            style={{ backgroundColor: "#f3f8f5", borderColor: "#d9e1dd", flex: 1 }}
          />
          {record.raw_value > 0 && record.normalized_value !== record.raw_value && (
            <span style={{ fontSize: 13, color: "#627268", fontWeight: 600 }}>
              × {+(record.normalized_value / record.raw_value).toFixed(4)}
            </span>
          )}
        </div>
      </label>
      <label>
        Normalized value (converted)
        <input
          type="number"
          value={form.normalized_value ?? ""}
          disabled={locked}
          onChange={(event) => setForm({ ...form, normalized_value: event.target.value })}
        />
      </label>
      <label>
        Unit
        <input
          value={form.normalized_unit || ""}
          disabled={locked}
          onChange={(event) => setForm({ ...form, normalized_unit: event.target.value })}
        />
      </label>
      <label>
        Location
        <input
          value={form.location_name || ""}
          disabled={locked}
          onChange={(event) => setForm({ ...form, location_name: event.target.value })}
        />
      </label>
      <label>
        Review comment
        <textarea
          value={form.review_comment || ""}
          disabled={locked}
          onChange={(event) => setForm({ ...form, review_comment: event.target.value })}
        />
      </label>

      <div className="detailActions">
        <button onClick={save} disabled={locked}>
          Save
        </button>
        <button className="primary iconText" onClick={approve} disabled={locked}>
          <CheckCircle2 size={16} /> Approve
        </button>
      </div>

      <h3>Raw Source Row</h3>
      <pre
  style={{
    height: "150px",
    overflow: "auto",
  }}
>
  {JSON.stringify(record.raw_data, null, 2)}
</pre>

      <h3>Activity</h3>
      <div className="activityList">
        {(Array.isArray(activity) ? activity : []).map((log) => (
          <div key={log.id}>
            <strong>{log.action_type}</strong>
            <span>{new Date(log.acted_at).toLocaleString()}</span>
          </div>
        ))}
        {!(Array.isArray(activity) ? activity : []).length && <p>No activity yet.</p>}
      </div>
    </section>
  );
}
