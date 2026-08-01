import type { QueryResponse } from '../types/api'
import { DataTable } from './DataTable'
import { ChartView } from './ChartView'

interface QueryResultProps {
  response: QueryResponse
}

export function QueryResult({ response }: QueryResultProps) {
  if (response.execution.status === 'error' || response.error) {
    return (
      <div className="query-error" data-testid="query-error">
        <h4>Query failed</h4>
        <p>{response.error?.message ?? 'An error occurred while executing the query.'}</p>
        {response.generated_query && (
          <details>
            <summary>Generated query</summary>
            <pre>{response.generated_query}</pre>
          </details>
        )}
      </div>
    )
  }

  const chartType = response.visualization?.chart_type ?? 'table'
  const rows = response.data?.rows ?? []
  const columns = response.data?.columns ?? []

  return (
    <div className="query-result" data-testid="query-result">
      {response.visualization?.title && (
        <h4 data-testid="viz-title">{response.visualization.title}</h4>
      )}
      <div className="execution-meta" data-testid="execution-meta">
        {response.execution.row_count != null && (
          <span>{response.execution.row_count} rows</span>
        )}
        {response.execution.duration_ms != null && (
          <span>{response.execution.duration_ms} ms</span>
        )}
        {response.execution.truncated && <span>Truncated</span>}
      </div>
      {chartType === 'metric' && rows.length > 0 ? (
        <div className="metric-card" data-testid="metric-card">
          <span className="metric-value">
            {String(
              rows[0][
                response.visualization?.y_axis?.field ??
                  columns[0]?.name ??
                  Object.keys(rows[0])[0]
              ],
            )}
          </span>
          <span className="metric-label">
            {response.visualization?.y_axis?.label ?? columns[0]?.name}
          </span>
        </div>
      ) : chartType !== 'table' && rows.length > 0 ? (
        <ChartView visualization={response.visualization!} rows={rows} />
      ) : (
        <DataTable columns={columns} rows={rows} />
      )}
      {response.generated_query && (
        <details className="generated-query">
          <summary>Generated query</summary>
          <pre data-testid="generated-query">{response.generated_query}</pre>
        </details>
      )}
      {response.follow_up_questions && response.follow_up_questions.length > 0 && (
        <div className="follow-ups" data-testid="follow-up-questions">
          <p>Suggested follow-ups:</p>
          <ul>
            {response.follow_up_questions.map((q) => (
              <li key={q}>{q}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
