import { createContext, useContext, type ReactNode } from 'react'
import { createApiClient, type ApiClient } from '../api/client'

export interface WidgetConfig {
  apiBaseUrl: string
  accessToken: string
  locale?: string
}

interface WidgetContextValue extends WidgetConfig {
  api: ApiClient
}

const WidgetContext = createContext<WidgetContextValue | null>(null)

export function WidgetProvider({
  apiBaseUrl,
  accessToken,
  locale,
  children,
}: WidgetConfig & { children: ReactNode }) {
  const value: WidgetContextValue = {
    apiBaseUrl,
    accessToken,
    locale,
    api: createApiClient(apiBaseUrl),
  }

  return <WidgetContext.Provider value={value}>{children}</WidgetContext.Provider>
}

export function useWidget(): WidgetContextValue {
  const ctx = useContext(WidgetContext)
  if (!ctx) {
    throw new Error('useWidget must be used within WidgetProvider or ConversationalBIWidget')
  }
  return ctx
}
