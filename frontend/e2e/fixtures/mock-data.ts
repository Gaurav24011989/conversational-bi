export const MOCK_USER = {
  id: 'user-11111111-1111-1111-1111-111111111111',
  email: 'analyst@example.com',
  full_name: 'Test Analyst',
  org_id: 'org-22222222-2222-2222-2222-222222222222',
  is_active: true,
  preferred_locale: 'en',
}

export const MOCK_TOKEN = 'mock-jwt-token'

export const MOCK_PROJECT = {
  id: 'proj-33333333-3333-3333-3333-333333333333',
  org_id: MOCK_USER.org_id,
  name: 'Default Project',
  description: 'Primary analytics workspace',
  created_at: '2025-01-15T10:00:00Z',
}

export const MOCK_PROJECT_2 = {
  id: 'proj-44444444-4444-4444-4444-444444444444',
  org_id: MOCK_USER.org_id,
  name: 'Sales Analytics',
  description: null,
  created_at: '2025-02-01T12:00:00Z',
}

export const MOCK_DATASOURCE = {
  id: 'ds-55555555-5555-5555-5555-555555555555',
  project_id: MOCK_PROJECT.id,
  name: 'Production Postgres',
  type: 'postgresql' as const,
  is_active: true,
  allowed_tables: null,
  created_at: '2025-01-16T08:00:00Z',
}

export const MOCK_CONVERSATION = {
  id: 'conv-66666666-6666-6666-6666-666666666666',
  project_id: MOCK_PROJECT.id,
  datasource_id: MOCK_DATASOURCE.id,
  user_id: MOCK_USER.id,
  title: null,
  created_at: '2025-03-01T14:00:00Z',
}

export const MOCK_QUERY_RESPONSE = {
  message_id: 'msg-77777777-7777-7777-7777-777777777777',
  conversation_id: MOCK_CONVERSATION.id,
  role: 'assistant' as const,
  type: 'query_result' as const,
  natural_language_query: 'Show monthly revenue for 2025',
  generated_query: 'SELECT month, revenue FROM sales WHERE year = 2025',
  query_language: 'sql',
  datasource: {
    id: MOCK_DATASOURCE.id,
    name: MOCK_DATASOURCE.name,
    dialect: 'postgresql',
  },
  execution: {
    status: 'success' as const,
    row_count: 3,
    duration_ms: 42,
    truncated: false,
  },
  data: {
    columns: [
      { name: 'month', type: 'text' },
      { name: 'revenue', type: 'numeric' },
    ],
    rows: [
      { month: 'Jan', revenue: 12000 },
      { month: 'Feb', revenue: 15000 },
      { month: 'Mar', revenue: 18000 },
    ],
  },
  visualization: {
    chart_type: 'bar' as const,
    title: 'Monthly Revenue (2025)',
    x_axis: { field: 'month', label: 'Month' },
    y_axis: { field: 'revenue', label: 'Revenue' },
    series: [{ field: 'revenue' }],
    reasoning: 'Bar chart for categorical comparison',
  },
  follow_up_questions: ['Break down by product category?', 'Compare with 2024?'],
}

export const MOCK_CLARIFICATION = {
  message_id: 'msg-88888888-8888-8888-8888-888888888888',
  conversation_id: MOCK_CONVERSATION.id,
  role: 'assistant' as const,
  type: 'clarification' as const,
  questions: ['Which time period?', 'Which metric should I use?'],
}

export const MOCK_QUERY_ERROR = {
  ...MOCK_QUERY_RESPONSE,
  message_id: 'msg-99999999-9999-9999-9999-999999999999',
  execution: { status: 'error' as const, row_count: 0, duration_ms: 10 },
  data: null,
  visualization: null,
  error: { code: 'QUERY_ERROR', message: 'Table "unknown_table" does not exist' },
}

export const MOCK_LOCALES = {
  default_locale: 'en',
  supported_locales: [
    { code: 'en', name: 'English', native_name: 'English' },
    { code: 'fr', name: 'French', native_name: 'Français' },
  ],
}
