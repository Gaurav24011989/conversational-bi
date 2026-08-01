import type { CSSProperties } from 'react'
import { ConversationChat, type ConversationChatProps } from './components/ConversationChat'
import { WidgetProvider } from './context/WidgetContext'
import type { ConversationResponse } from './types/api'
import './styles/widget.css'

export interface ConversationalBIWidgetProps
  extends Omit<ConversationChatProps, 'onError' | 'onConversationCreated'> {
  /** Backend API origin, e.g. https://api.example.com */
  apiBaseUrl: string
  /** JWT access token from POST /api/v1/auth/login */
  accessToken: string
  /** Optional BCP-47 locale passed to message requests */
  locale?: string
  /** Container height (default 560px) */
  height?: number | string
  /** Additional class name on the root element */
  className?: string
  /** Inline styles on the root element */
  style?: CSSProperties
  /** Called when the widget encounters an API or runtime error */
  onError?: (error: Error) => void
  /** Called when a new conversation is created (when conversationId is omitted) */
  onConversationCreated?: (conversation: ConversationResponse) => void
}

export function ConversationalBIWidget({
  apiBaseUrl,
  accessToken,
  locale,
  height = 560,
  className,
  style,
  projectId,
  datasourceId,
  conversationId,
  title,
  onError,
  onConversationCreated,
}: ConversationalBIWidgetProps) {
  const rootClassName = ['cbi-widget', className].filter(Boolean).join(' ')

  return (
    <WidgetProvider apiBaseUrl={apiBaseUrl} accessToken={accessToken} locale={locale}>
      <div
        className={rootClassName}
        style={{ height, ...style }}
        data-testid="conversational-bi-widget"
      >
        <ConversationChat
          projectId={projectId}
          datasourceId={datasourceId}
          conversationId={conversationId}
          title={title}
          onError={onError}
          onConversationCreated={onConversationCreated}
        />
      </div>
    </WidgetProvider>
  )
}
