export type DataSourceType = 'postgresql' | 'mysql' | 'mongodb' | 'elasticsearch'

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

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface UserResponse {
  id: string
  email: string
  full_name: string | null
  org_id: string
  is_active: boolean
  preferred_locale: string | null
}

export interface ProjectResponse {
  id: string
  org_id: string
  name: string
  description: string | null
  created_at: string
}

export interface DataSourceConfig {
  host: string
  port: number
  database: string
  username?: string
  password?: string
  schema_name?: string | null
  ssl_mode?: string | null
  auth_source?: string | null
}

export interface DataSourceResponse {
  id: string
  project_id: string
  name: string
  type: DataSourceType
  is_active: boolean
  allowed_tables: string[] | null
  created_at: string
}

export interface ConnectionTestResponse {
  success: boolean
  message: string
  latency_ms: number | null
}

export interface SchemaColumn {
  name: string
  data_type: string
  nullable: boolean
  is_pk: boolean
}

export interface SchemaEntity {
  name: string
  type: 'table' | 'collection'
  columns: SchemaColumn[]
  relationships: Array<{
    column: string
    ref_table: string
    ref_column: string
  }>
  sample_rows: Record<string, unknown>[]
}

export interface SchemaSnapshotResponse {
  id: string
  datasource_id: string
  version: number
  schema_data: { entities: SchemaEntity[] }
  captured_at: string
}

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

export interface LocaleInfo {
  code: string
  name: string
  native_name: string
}

export interface LocalesResponse {
  default_locale: string
  supported_locales: LocaleInfo[]
}

export interface ApiError {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>
}
