export default function Summary({ summary }) {
  const statusCounts = summary?.status_counts || {};

  return (
    <section className="panel">
      <h2>Overview</h2>
      <div className="metricGrid">
        <Metric label="Batches" value={summary?.batches || 0} />
        <Metric label="Records" value={summary?.records || 0} />
        <Metric label="Failed Rows" value={summary?.raw_failures || 0} tone="bad" />
        <Metric label="Flagged" value={statusCounts.FLAGGED || 0} tone="warn" />
      </div>
    </section>
  );
}

function Metric({ label, value, tone = "" }) {
  return (
    <div className={`metric ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
