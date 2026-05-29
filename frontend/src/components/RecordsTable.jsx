import StatusBadge from "./StatusBadge.jsx";
import { formatNumber } from "../utils.js";
import { Lock } from "lucide-react";

function getOriginalString(record) {
  if (!record.raw_data) return null;
  if (record.source_type === "SAP") return record.raw_data.quantity || record.raw_data.menge || record.raw_data.bestellmenge;
  if (record.source_type === "UTILITY") return record.raw_data.consumption || record.raw_data.usage || record.raw_data.usage_kwh;
  if (record.source_type === "TRAVEL") return record.raw_data.distance_km || record.raw_data.nights;
  return null;
}

export default function RecordsTable({ records, selected, onSelect, onLock }) {
  return (
    <div className="tableWrap">
      <table>
        <thead>
          <tr>
            <th>Source</th>
            <th>Category</th>
            <th>Scope</th>
            <th>Value</th>
            <th>Location</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {(Array.isArray(records) ? records : []).map((record) => (
            <tr
              key={record.id}
              className={selected?.id === record.id ? "selected" : ""}
              onClick={() => onSelect(record)}
            >
              <td>{record.source_type}</td>
              <td>{record.activity_category}</td>
              <td>{record.scope}</td>
              <td>
                <div style={{ fontWeight: 600 }}>
                  {formatNumber(record.normalized_value)} {record.normalized_unit}
                </div>
                {(()=>{
                  const origStr = getOriginalString(record);
                  const showOrig = origStr && record.raw_value !== undefined && record.raw_value !== null && origStr !== record.raw_value.toString();
                  const showUnitChange = record.raw_unit?.toLowerCase() !== record.normalized_unit?.toLowerCase();
                  const showValChange = record.raw_value !== record.normalized_value;
                  
                  if (!showOrig && !showUnitChange && !showValChange) return null;
                  
                  return (
                    <div style={{ fontSize: 11, color: "#627268", marginTop: 4 }}>
                      (from {showOrig ? `"${origStr}"` : formatNumber(record.raw_value)} {record.raw_unit}
                      {record.raw_value > 0 && record.normalized_value !== record.raw_value 
                        ? ` × ${+(record.normalized_value / record.raw_value).toFixed(4)}` 
                        : ''})
                    </div>
                  );
                })()}
              </td>
              <td>{record.location_name || record.location_raw || "-"}</td>
              <td>
                {record.status === "APPROVED" ? (
                  <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                    <StatusBadge status={record.status} />
                    <button 
                       className="iconText" 
                       style={{ fontSize: 11, padding: "2px 6px" }} 
                       onClick={(e) => { 
                         e.stopPropagation(); 
                         onLock(record.id); 
                       }}
                    >
                      <Lock size={12} /> Lock
                    </button>
                  </div>
                ) : (
                  <StatusBadge status={record.status} />
                )}
              </td>
            </tr>
          ))}
          {!(Array.isArray(records) ? records : []).length && (
            <tr>
              <td colSpan="6" className="emptyCell">
                No rows in this view.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
