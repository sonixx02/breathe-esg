import { Lock } from "lucide-react";

export default function BatchList({ api, batches, reload, setMessage }) {
  async function lockBatch(batchId) {
    try {
      const result = await api(`/batches/${batchId}/lock/`, { method: "POST" });
      setMessage(`Locked ${result.locked_records} approved records.`);
      await reload();
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <section className="panel">
      <h2>Batches</h2>
      <div className="batchList">
        {(Array.isArray(batches) ? batches : []).slice(0, 8).map((batch) => (
          <div className="batchRow" key={batch.id}>
            <div>
              <strong>{batch.source_type}</strong>
              <span>{batch.file_name}</span>
              <small>
                {batch.parsed_rows} parsed / {batch.failed_rows} failed
              </small>
            </div>
            <button className="iconText" style={{fontSize: 11, padding: "4px 8px"}} title="Lock approved records in this batch" onClick={() => lockBatch(batch.id)}>
              <Lock size={12} /> Lock Approved
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
