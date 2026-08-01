interface DataTableProps {
  columns: Array<{ name: string; type: string }>
  rows: Array<Record<string, unknown>>
}

export function DataTable({ columns, rows }: DataTableProps) {
  if (rows.length === 0) {
    return <p className="empty-state" data-testid="empty-table">No data returned.</p>
  }

  const colNames = columns.length > 0 ? columns.map((c) => c.name) : Object.keys(rows[0])

  return (
    <div className="table-wrap" data-testid="data-table">
      <table>
        <thead>
          <tr>
            {colNames.map((name) => (
              <th key={name}>{name}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {colNames.map((name) => (
                <td key={name}>{formatCell(row[name])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function formatCell(value: unknown): string {
  if (value == null) return ''
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
