export type ChartType =
  | 'table'
  | 'bar'
  | 'line'
  | 'area'
  | 'pie'
  | 'donut'
  | 'scatter'
  | 'metric'
  | 'heatmap'

export interface ConversationResponse {
  id: string
  project_id: string
  datasource_id: string
  user_id: string
  title: string | null
  created_at: string
}

export interface MessageResponse {
  id: string
  conversation_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  response_data: QueryResponse | ClarificationResponse | null
  created_at: string
}

export interface QueryResponse {
  message_id: string
  conversation_id: string
  role: 'assistant'
  type: 'query_result'
  locale?: string | null
  natural_language_query: string
  generated_query?: string | null
  query_language?: string | null
  datasource?: {
    id: string
    name: string
    dialect: string
  } | null
  execution: {
    status: 'success' | 'error'
    row_count?: number | null
    duration_ms?: number | null
    truncated?: boolean
  }
  data?: {
    columns: Array<{ name: string; type: string }>
    rows: Array<Record<string, unknown>>
  } | null
  visualization?: {
    chart_type: ChartType
    title?: string | null
    x_axis?: { field: string; label?: string | null } | null
    y_axis?: { field: string; label?: string | null } | null
    series?: Array<{ field: string; label?: string | null }>
    reasoning?: string | null
  } | null
  follow_up_questions?: string[]
  trace_id?: string | null
  error?: { code: string; message: string } | null
}

export interface ClarificationResponse {
  message_id: string
  conversation_id: string
  role: 'assistant'
  type: 'clarification'
  questions: string[]
  trace_id?: string | null
}

export interface ApiError {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>
}
