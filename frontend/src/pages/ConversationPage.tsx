import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, ApiClientError } from '../api/client'
import { QueryResult } from '../components/QueryResult'
import { useAuth } from '../context/AuthContext'
import {
  addStoredConversation,
  updateStoredConversationTitle,
} from '../utils/storage'
import type {
  ClarificationResponse,
  ConversationResponse,
  MessageResponse,
  QueryResponse,
} from '../types/api'

export function ConversationPage() {
  const { projectId, conversationId } = useParams<{
    projectId: string
    conversationId: string
  }>()
  const { token } = useAuth()
  const [conversation, setConversation] = useState<ConversationResponse | null>(null)
  const [messages, setMessages] = useState<MessageResponse[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!token || !conversationId) return
    setLoading(true)
    Promise.all([
      api.getConversation(token, conversationId),
      api.listMessages(token, conversationId),
    ])
      .then(([conv, msgs]) => {
        setConversation(conv)
        setMessages(msgs)
        addStoredConversation({
          id: conv.id,
          projectId: conv.project_id,
          datasourceId: conv.datasource_id,
          title: conv.title,
          createdAt: conv.created_at,
        })
      })
      .catch((err) =>
        setError(err instanceof ApiClientError ? err.message : 'Failed to load conversation'),
      )
      .finally(() => setLoading(false))
  }, [token, conversationId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend(e: FormEvent) {
    e.preventDefault()
    if (!token || !conversationId || !input.trim()) return
    const content = input.trim()
    const isFirstMessage = messages.length === 0
    setInput('')
    setSending(true)
    setError(null)

    const optimisticUser: MessageResponse = {
      id: `temp-${Date.now()}`,
      conversation_id: conversationId,
      role: 'user',
      content,
      response_data: null,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, optimisticUser])

    try {
      const response = await api.sendMessage(token, conversationId, { content })
      const assistant: MessageResponse = {
        id: response.message_id,
        conversation_id: response.conversation_id,
        role: 'assistant',
        content:
          response.type === 'clarification'
            ? (response as ClarificationResponse).questions.join('\n')
            : (response as QueryResponse).natural_language_query,
        response_data: response,
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistant])
      if (isFirstMessage) {
        updateStoredConversationTitle(conversationId, content)
      }
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to send message')
    } finally {
      setSending(false)
    }
  }

  function handleFollowUp(question: string) {
    setInput(question)
  }

  if (loading) {
    return <p data-testid="conversation-loading">Loading conversation…</p>
  }

  if (!conversation) {
    return <p data-testid="conversation-not-found">Conversation not found.</p>
  }

  return (
    <div className="page conversation-page" data-testid="conversation-page">
      <div className="page-header">
        <div>
          <Link to={`/projects/${projectId}`} className="back-link">
            ← Back to project
          </Link>
          <h1>{conversation.title ?? 'Conversation'}</h1>
        </div>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" data-testid="conversation-error">
          {error}
        </div>
      )}

      <div className="messages-panel" data-testid="messages-panel">
        {messages.length === 0 ? (
          <div className="empty-state" data-testid="messages-empty">
            <p>Ask a question in natural language to query your data.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`message message-${msg.role}`}
              data-testid={`message-${msg.role}`}
            >
              <div className="message-bubble">
                <span className="message-role">{msg.role}</span>
                {msg.role === 'user' ? (
                  <p>{msg.content}</p>
                ) : msg.response_data?.type === 'clarification' ? (
                  <div data-testid="clarification-response">
                    <p>I need a bit more information:</p>
                    <ul>
                      {(msg.response_data as ClarificationResponse).questions.map((q) => (
                        <li key={q}>
                          <button
                            type="button"
                            className="link-button"
                            onClick={() => handleFollowUp(q)}
                            data-testid="clarification-question"
                          >
                            {q}
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : msg.response_data?.type === 'query_result' ? (
                  <QueryResult response={msg.response_data as QueryResponse} />
                ) : (
                  <p>{msg.content}</p>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <form className="message-form" onSubmit={handleSend} data-testid="message-form">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your data…"
          rows={2}
          disabled={sending}
          data-testid="message-input"
        />
        <button type="submit" disabled={sending || !input.trim()} data-testid="message-submit">
          {sending ? 'Sending…' : 'Send'}
        </button>
      </form>
    </div>
  )
}
