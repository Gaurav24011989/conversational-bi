import type {
  ApiError,
  ClarificationResponse,
  ConversationResponse,
  MessageResponse,
  QueryResponse,
} from '../types/api'

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

function apiUrl(apiBaseUrl: string, path: string): string {
  const base = apiBaseUrl.replace(/\/$/, '')
  return `${base}/api/v1${path}`
}

async function request<T>(
  apiBaseUrl: string,
  path: string,
  options: RequestInit & { token?: string | null } = {},
): Promise<T> {
  const { token, headers, ...rest } = options
  const response = await fetch(apiUrl(apiBaseUrl, path), {
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

export function createApiClient(apiBaseUrl: string) {
  return {
    createConversation: (
      token: string,
      projectId: string,
      body: { datasource_id: string; title?: string },
    ) =>
      request<ConversationResponse>(apiBaseUrl, `/projects/${projectId}/conversations`, {
        method: 'POST',
        token,
        body: JSON.stringify(body),
      }),

    getConversation: (token: string, conversationId: string) =>
      request<ConversationResponse>(apiBaseUrl, `/conversations/${conversationId}`, { token }),

    sendMessage: (
      token: string,
      conversationId: string,
      body: { content: string; locale?: string },
    ) =>
      request<QueryResponse | ClarificationResponse>(
        apiBaseUrl,
        `/conversations/${conversationId}/messages`,
        {
          method: 'POST',
          token,
          body: JSON.stringify(body),
        },
      ),

    listMessages: (token: string, conversationId: string) =>
      request<MessageResponse[]>(apiBaseUrl, `/conversations/${conversationId}/messages`, {
        token,
      }),
  }
}

export type ApiClient = ReturnType<typeof createApiClient>
