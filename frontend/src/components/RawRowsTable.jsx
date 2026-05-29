export default function RawRowsTable({ rows }) {
  return (
    <div className="tableWrap">
      <table>
        <thead>
          <tr>
            <th>Source</th>
            <th>File</th>
            <th>Row</th>
            <th>Error</th>
            <th>Raw Data</th>
          </tr>
        </thead>
        <tbody>
          {(Array.isArray(rows) ? rows : []).map((row) => (
            <tr key={row.id}>
              <td>{row.source_type}</td>
              <td>{row.file_name}</td>
              <td>{row.row_number}</td>
              <td>{row.parse_error}</td>
              <td className="rawText">{JSON.stringify(row.raw_data)}</td>
            </tr>
          ))}
          {!(Array.isArray(rows) ? rows : []).length && (
            <tr>
              <td colSpan="5" className="emptyCell">
                No failed rows in this view.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
