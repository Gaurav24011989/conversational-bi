const TOKEN_KEY = 'cbi_access_token'
const CONVERSATIONS_KEY = 'cbi_conversations'

export const MAX_STORED_CONVERSATIONS = 5

export interface StoredConversation {
  id: string
  projectId: string
  datasourceId: string
  title: string | null
  createdAt: string
  lastAccessedAt: string
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

function readAllConversations(): StoredConversation[] {
  try {
    const raw = localStorage.getItem(CONVERSATIONS_KEY)
    if (!raw) return []
    return (JSON.parse(raw) as StoredConversation[]).map(normalizeConversation)
  } catch {
    return []
  }
}

function normalizeConversation(conversation: StoredConversation): StoredConversation {
  return {
    ...conversation,
    lastAccessedAt: conversation.lastAccessedAt ?? conversation.createdAt,
  }
}

function writeAllConversations(all: StoredConversation[]): void {
  localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(trimAllProjects(all)))
}

function trimAllProjects(all: StoredConversation[]): StoredConversation[] {
  const byProject = new Map<string, StoredConversation[]>()

  for (const conversation of all) {
    const projectConversations = byProject.get(conversation.projectId) ?? []
    projectConversations.push(conversation)
    byProject.set(conversation.projectId, projectConversations)
  }

  const trimmed: StoredConversation[] = []
  for (const projectConversations of byProject.values()) {
    const sorted = projectConversations.sort(
      (a, b) => new Date(b.lastAccessedAt).getTime() - new Date(a.lastAccessedAt).getTime(),
    )
    trimmed.push(...sorted.slice(0, MAX_STORED_CONVERSATIONS))
  }

  return trimmed
}

export function getStoredConversations(projectId: string): StoredConversation[] {
  return readAllConversations()
    .filter((conversation) => conversation.projectId === projectId)
    .sort(
      (a, b) => new Date(b.lastAccessedAt).getTime() - new Date(a.lastAccessedAt).getTime(),
    )
    .slice(0, MAX_STORED_CONVERSATIONS)
}

export function addStoredConversation(
  conversation: Omit<StoredConversation, 'lastAccessedAt'> & { lastAccessedAt?: string },
): void {
  const now = new Date().toISOString()
  const entry: StoredConversation = {
    ...conversation,
    lastAccessedAt: conversation.lastAccessedAt ?? now,
  }
  const all = readAllConversations().filter((stored) => stored.id !== entry.id)
  all.push(entry)
  writeAllConversations(all)
}

export function touchStoredConversation(conversationId: string): void {
  const all = readAllConversations()
  const index = all.findIndex((conversation) => conversation.id === conversationId)
  if (index === -1) return

  all[index] = { ...all[index], lastAccessedAt: new Date().toISOString() }
  writeAllConversations(all)
}

export function updateStoredConversationTitle(conversationId: string, title: string): void {
  const all = readAllConversations()
  const index = all.findIndex((conversation) => conversation.id === conversationId)
  if (index === -1) return

  all[index] = { ...all[index], title, lastAccessedAt: new Date().toISOString() }
  writeAllConversations(all)
}

export function removeStoredConversation(conversationId: string): void {
  const all = readAllConversations().filter((conversation) => conversation.id !== conversationId)
  writeAllConversations(all)
}
