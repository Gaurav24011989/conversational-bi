import type {
  ApiError,
  ClarificationResponse,
  ConnectionTestResponse,
  ConversationResponse,
  DataSourceConfig,
  DataSourceResponse,
  DataSourceType,
  LocalesResponse,
  MessageResponse,
  ProjectResponse,
  QueryResponse,
  SchemaSnapshotResponse,
  TokenResponse,
  UserResponse,
} from '../types/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

function apiUrl(path: string): string {
  const base = API_BASE.replace(/\/$/, '')
  return `${base}/api/v1${path}`
}

export class ApiClientError extends Error {
  status: number
  detail: unknown

  constructor(status: number, detail: unknown) {
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => d.msg).join(', ')
          : 'Request failed'
    super(message)
    this.status = status
    this.detail = detail
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { token?: string | null } = {},
): Promise<T> {
  const { token, headers, ...rest } = options
  const response = await fetch(apiUrl(path), {
    ...rest,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(headers || {}),
    },
  })

  if (!response.ok) {
    let detail: unknown = 'Request failed'
    try {
      const body = (await response.json()) as ApiError
      detail = body.detail ?? detail
    } catch {
      // ignore parse errors
    }
    throw new ApiClientError(response.status, detail)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export const api = {
  register: (body: {
    email: string
    password: string
    full_name?: string
    org_name: string
    org_slug: string
  }) =>
    request<TokenResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  login: (body: { email: string; password: string }) =>
    request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  me: (token: string) => request<UserResponse>('/auth/me', { token }),

  updateLocale: (token: string, preferred_locale: string) =>
    request<UserResponse>('/auth/me/locale', {
      method: 'PATCH',
      token,
      body: JSON.stringify({ preferred_locale }),
    }),

  locales: () => request<LocalesResponse>('/locales'),

  listProjects: (token: string, orgId: string) =>
    request<ProjectResponse[]>(`/orgs/${orgId}/projects`, { token }),

  createProject: (
    token: string,
    orgId: string,
    body: { name: string; description?: string },
  ) =>
    request<ProjectResponse>(`/orgs/${orgId}/projects`, {
      method: 'POST',
      token,
      body: JSON.stringify(body),
    }),

  getProject: (token: string, projectId: string) =>
    request<ProjectResponse>(`/projects/${projectId}`, { token }),

  listDatasources: (token: string, projectId: string) =>
    request<DataSourceResponse[]>(`/projects/${projectId}/datasources`, { token }),

  createDatasource: (
    token: string,
    projectId: string,
    body: {
      name: string
      type: DataSourceType
      config: DataSourceConfig
      allowed_tables?: string[]
    },
  ) =>
    request<DataSourceResponse>(`/projects/${projectId}/datasources`, {
      method: 'POST',
      token,
      body: JSON.stringify(body),
    }),

  testDatasource: (token: string, datasourceId: string) =>
    request<ConnectionTestResponse>(`/datasources/${datasourceId}/test`, {
      method: 'POST',
      token,
    }),

  refreshSchema: (token: string, datasourceId: string) =>
    request<SchemaSnapshotResponse>(`/datasources/${datasourceId}/schema/refresh`, {
      method: 'POST',
      token,
    }),

  getSchema: (token: string, datasourceId: string) =>
    request<SchemaSnapshotResponse>(`/datasources/${datasourceId}/schema`, { token }),

  createConversation: (
    token: string,
    projectId: string,
    body: { datasource_id: string; title?: string },
  ) =>
    request<ConversationResponse>(`/projects/${projectId}/conversations`, {
      method: 'POST',
      token,
      body: JSON.stringify(body),
    }),

  getConversation: (token: string, conversationId: string) =>
    request<ConversationResponse>(`/conversations/${conversationId}`, { token }),

  sendMessage: (
    token: string,
    conversationId: string,
    body: { content: string; locale?: string },
  ) =>
    request<QueryResponse | ClarificationResponse>(`/conversations/${conversationId}/messages`, {
      method: 'POST',
      token,
      body: JSON.stringify(body),
    }),

  listMessages: (token: string, conversationId: string) =>
    request<MessageResponse[]>(`/conversations/${conversationId}/messages`, { token }),

  health: async () => {
    const base = API_BASE.replace(/\/$/, '')
    const response = await fetch(`${base}/health`)
    return response.json() as Promise<{ status: string; service: string }>
  },
}
