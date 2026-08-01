import type { Page, Route } from '@playwright/test'
import {
  MOCK_CLARIFICATION,
  MOCK_CONVERSATION,
  MOCK_DATASOURCE,
  MOCK_LOCALES,
  MOCK_PROJECT,
  MOCK_PROJECT_2,
  MOCK_QUERY_ERROR,
  MOCK_QUERY_RESPONSE,
  MOCK_TOKEN,
  MOCK_USER,
} from './mock-data'

type MockOptions = {
  authenticated?: boolean
  projects?: typeof MOCK_PROJECT[]
  datasources?: typeof MOCK_DATASOURCE[]
  messages?: unknown[]
  messageResponse?: unknown
  loginFails?: boolean
  registerFails?: boolean
  unauthorized?: boolean
}

function json(route: Route, status: number, body: unknown) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })
}

export async function setupApiMocks(page: Page, options: MockOptions = {}) {
  const {
    authenticated = false,
    projects = [MOCK_PROJECT, MOCK_PROJECT_2],
    datasources = [MOCK_DATASOURCE],
    messages = [],
    messageResponse = MOCK_QUERY_RESPONSE,
    loginFails = false,
    registerFails = false,
    unauthorized = false,
  } = options

  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url())
    const path = url.pathname.replace(/.*\/api\/v1/, '')
    const method = route.request().method()
    const auth = route.request().headers()['authorization']

    if (unauthorized && auth) {
      return json(route, 401, { detail: 'Invalid credentials' })
    }

    if (path === '/auth/login' && method === 'POST') {
      if (loginFails) {
        return json(route, 401, { detail: 'Invalid credentials' })
      }
      return json(route, 200, { access_token: MOCK_TOKEN, token_type: 'bearer' })
    }

    if (path === '/auth/register' && method === 'POST') {
      if (registerFails) {
        return json(route, 400, { detail: 'Organization slug already exists' })
      }
      return json(route, 201, { access_token: MOCK_TOKEN, token_type: 'bearer' })
    }

    if (path === '/auth/me' && method === 'GET') {
      if (!auth && !authenticated) {
        return json(route, 401, { detail: 'Not authenticated' })
      }
      return json(route, 200, MOCK_USER)
    }

    if (path === '/locales' && method === 'GET') {
      return json(route, 200, MOCK_LOCALES)
    }

    if (path === `/orgs/${MOCK_USER.org_id}/projects` && method === 'GET') {
      return json(route, 200, projects)
    }

    if (path === `/orgs/${MOCK_USER.org_id}/projects` && method === 'POST') {
      const body = route.request().postDataJSON() as { name: string; description?: string }
      return json(route, 201, {
        id: 'proj-new-new-new-new-newnewnewnew',
        org_id: MOCK_USER.org_id,
        name: body.name,
        description: body.description ?? null,
        created_at: new Date().toISOString(),
      })
    }

    if (path === `/projects/${MOCK_PROJECT.id}` && method === 'GET') {
      return json(route, 200, MOCK_PROJECT)
    }

    if (path === `/projects/${MOCK_PROJECT.id}/datasources` && method === 'GET') {
      return json(route, 200, datasources)
    }

    if (path === `/projects/${MOCK_PROJECT.id}/datasources` && method === 'POST') {
      const body = route.request().postDataJSON() as { name: string; type: string }
      return json(route, 201, {
        id: 'ds-new-new-new-new-newnewnewnewnew',
        project_id: MOCK_PROJECT.id,
        name: body.name,
        type: body.type,
        is_active: true,
        allowed_tables: null,
        created_at: new Date().toISOString(),
      })
    }

    if (path.match(/^\/datasources\/[^/]+\/test$/) && method === 'POST') {
      return json(route, 200, { success: true, message: 'OK', latency_ms: 12 })
    }

    if (path.match(/^\/datasources\/[^/]+\/schema\/refresh$/) && method === 'POST') {
      return json(route, 200, {
        id: 'schema-1',
        datasource_id: MOCK_DATASOURCE.id,
        version: 1,
        schema_data: { entities: [] },
        captured_at: new Date().toISOString(),
      })
    }

    if (path === `/projects/${MOCK_PROJECT.id}/conversations` && method === 'POST') {
      return json(route, 201, MOCK_CONVERSATION)
    }

    if (path === `/conversations/${MOCK_CONVERSATION.id}` && method === 'GET') {
      return json(route, 200, MOCK_CONVERSATION)
    }

    if (path === `/conversations/${MOCK_CONVERSATION.id}/messages` && method === 'GET') {
      return json(route, 200, messages)
    }

    if (path === `/conversations/${MOCK_CONVERSATION.id}/messages` && method === 'POST') {
      const body = route.request().postDataJSON() as { content: string }
      if (body.content.toLowerCase().includes('clarify')) {
        return json(route, 200, MOCK_CLARIFICATION)
      }
      if (body.content.toLowerCase().includes('error')) {
        return json(route, 200, MOCK_QUERY_ERROR)
      }
      if (body.content.trim() === '') {
        return json(route, 422, { detail: [{ loc: ['body', 'content'], msg: 'too short', type: 'value_error' }] })
      }
      return json(route, 200, { ...messageResponse, natural_language_query: body.content })
    }

    return json(route, 404, { detail: `Unhandled mock: ${method} ${path}` })
  })
}

export async function loginAsMockUser(page: Page) {
  await setupApiMocks(page, { authenticated: true })
  await page.goto('/login')
  await page.getByTestId('login-email').fill(MOCK_USER.email)
  await page.getByTestId('login-password').fill('password123')
  await page.getByTestId('login-submit').click()
  await page.waitForURL('**/projects')
}
