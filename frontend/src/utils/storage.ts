const TOKEN_KEY = 'cbi_access_token'
const CONVERSATIONS_KEY = 'cbi_conversations'

export interface StoredConversation {
  id: string
  projectId: string
  datasourceId: string
  title: string | null
  createdAt: string
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export function getStoredConversations(projectId: string): StoredConversation[] {
  try {
    const raw = localStorage.getItem(CONVERSATIONS_KEY)
    if (!raw) return []
    const all = JSON.parse(raw) as StoredConversation[]
    return all.filter((c) => c.projectId === projectId)
  } catch {
    return []
  }
}

export function addStoredConversation(conversation: StoredConversation): void {
  const raw = localStorage.getItem(CONVERSATIONS_KEY)
  const all: StoredConversation[] = raw ? JSON.parse(raw) : []
  all.unshift(conversation)
  localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(all))
}

export function removeStoredConversation(conversationId: string): void {
  const raw = localStorage.getItem(CONVERSATIONS_KEY)
  if (!raw) return
  const all = (JSON.parse(raw) as StoredConversation[]).filter((c) => c.id !== conversationId)
  localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(all))
}
