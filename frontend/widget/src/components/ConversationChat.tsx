import { useEffect, useRef, useState, type FormEvent } from 'react'
import { ApiClientError } from '../api/client'
import { useWidget } from '../context/WidgetContext'
import type {
  ClarificationResponse,
  ConversationResponse,
  MessageResponse,
  QueryResponse,
} from '../types/api'
import { QueryResult } from './QueryResult'

export interface ConversationChatProps {
  projectId: string
  datasourceId: string
  conversationId?: string
  title?: string
  onError?: (error: Error) => void
  onConversationCreated?: (conversation: ConversationResponse) => void
}

export function ConversationChat({
  projectId,
  datasourceId,
  conversationId: initialConversationId,
  title,
  onError,
  onConversationCreated,
}: ConversationChatProps) {
  const { api, accessToken, locale } = useWidget()
  const [conversation, setConversation] = useState<ConversationResponse | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(
    initialConversationId ?? null,
  )
  const [messages, setMessages] = useState<MessageResponse[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const onErrorRef = useRef(onError)
  const onConversationCreatedRef = useRef(onConversationCreated)

  useEffect(() => {
    onErrorRef.current = onError
    onConversationCreatedRef.current = onConversationCreated
  }, [onError, onConversationCreated])

  useEffect(() => {
    let cancelled = false

    async function init() {
      setLoading(true)
      setError(null)

      try {
        let convId = initialConversationId

        if (!convId) {
          const conv = await api.createConversation(accessToken, projectId, {
            datasource_id: datasourceId,
            title,
          })
          if (cancelled) return
          convId = conv.id
          setConversationId(conv.id)
          setConversation(conv)
          onConversationCreatedRef.current?.(conv)
        } else {
          const conv = await api.getConversation(accessToken, convId)
          if (cancelled) return
          setConversationId(convId)
          setConversation(conv)
        }

        const msgs = await api.listMessages(accessToken, convId)
        if (cancelled) return
        setMessages(msgs)
      } catch (err) {
        if (cancelled) return
        const apiError =
          err instanceof ApiClientError
            ? err
            : err instanceof Error
              ? err
              : new Error('Failed to load conversation')
        setError(apiError.message)
        onErrorRef.current?.(apiError)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    init()
    return () => {
      cancelled = true
    }
  }, [accessToken, api, datasourceId, initialConversationId, projectId, title])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend(e: FormEvent) {
    e.preventDefault()
    if (!conversationId || !input.trim()) return
    const content = input.trim()
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
      const response = await api.sendMessage(accessToken, conversationId, {
        content,
        locale,
      })
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
    } catch (err) {
      const apiError =
        err instanceof ApiClientError
          ? err
          : err instanceof Error
            ? err
            : new Error('Failed to send message')
      setError(apiError.message)
      onError?.(apiError)
    } finally {
      setSending(false)
    }
  }

  function handleFollowUp(question: string) {
    setInput(question)
  }

  if (loading) {
    return (
      <div className="cbi-loading" data-testid="conversation-loading">
        Loading conversation…
      </div>
    )
  }

  if (!conversation) {
    return (
      <div className="cbi-error" data-testid="conversation-not-found">
        Conversation not found.
      </div>
    )
  }

  return (
    <div className="cbi-chat" data-testid="conversation-chat">
      <div className="cbi-chat-header">
        <h2 className="cbi-chat-title">{conversation.title ?? title ?? 'Ask your data'}</h2>
      </div>

      {error && (
        <div className="cbi-alert cbi-alert-error" role="alert" data-testid="conversation-error">
          {error}
        </div>
      )}

      <div className="cbi-messages-panel" data-testid="messages-panel">
        {messages.length === 0 ? (
          <div className="cbi-empty-state" data-testid="messages-empty">
            <p>Ask a question in natural language to query your data.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`cbi-message cbi-message-${msg.role}`}
              data-testid={`message-${msg.role}`}
            >
              <div className="cbi-message-bubble">
                <span className="cbi-message-role">{msg.role}</span>
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
                            className="cbi-link-button"
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
                  <QueryResult
                    response={msg.response_data as QueryResponse}
                    onFollowUp={handleFollowUp}
                  />
                ) : (
                  <p>{msg.content}</p>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <form className="cbi-message-form" onSubmit={handleSend} data-testid="message-form">
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
