import { expect, test } from '@playwright/test'
import { loginAsMockUser } from './fixtures/api-mocks'
import {
  MOCK_CONVERSATION,
  MOCK_DATASOURCE,
  MOCK_PROJECT,
  MOCK_QUERY_RESPONSE,
} from './fixtures/mock-data'

test.describe('Conversations', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsMockUser(page)
    await page.getByTestId(`project-card-${MOCK_PROJECT.id}`).click()
  })

  test('positive: start conversation and navigate to chat', async ({ page }) => {
    await page.getByTestId(`start-conversation-${MOCK_DATASOURCE.id}`).click()

    await expect(page).toHaveURL(
      new RegExp(`/projects/${MOCK_PROJECT.id}/conversations/${MOCK_CONVERSATION.id}`),
    )
    await expect(page.getByTestId('conversation-page')).toBeVisible()
    await expect(page.getByTestId('messages-empty')).toBeVisible()
  })

  test('positive: delete conversation from local history', async ({ page }) => {
    await page.evaluate(
      ({ conversation, projectId, datasourceId }) => {
        localStorage.setItem(
          'cbi_conversations',
          JSON.stringify([
            {
              id: conversation.id,
              projectId,
              datasourceId,
              title: 'Revenue analysis',
              createdAt: conversation.created_at,
              lastAccessedAt: conversation.created_at,
            },
          ]),
        )
      },
      {
        conversation: MOCK_CONVERSATION,
        projectId: MOCK_PROJECT.id,
        datasourceId: MOCK_DATASOURCE.id,
      },
    )
    await page.reload()

    await expect(page.getByTestId(`conversation-link-${MOCK_CONVERSATION.id}`)).toBeVisible()
    await page.getByTestId(`delete-conversation-${MOCK_CONVERSATION.id}`).click()
    await expect(page.getByTestId('conversations-empty')).toBeVisible()
    await expect(page.getByTestId(`conversation-link-${MOCK_CONVERSATION.id}`)).toHaveCount(0)
  })

  test('positive: continue existing conversation from local history', async ({ page }) => {
    await page.evaluate(
      ({ conversation, projectId, datasourceId }) => {
        localStorage.setItem(
          'cbi_conversations',
          JSON.stringify([
            {
              id: conversation.id,
              projectId,
              datasourceId,
              title: 'Saved conversation',
              createdAt: conversation.created_at,
              lastAccessedAt: conversation.created_at,
            },
          ]),
        )
      },
      {
        conversation: MOCK_CONVERSATION,
        projectId: MOCK_PROJECT.id,
        datasourceId: MOCK_DATASOURCE.id,
      },
    )
    await page.reload()

    await page.getByTestId(`conversation-link-${MOCK_CONVERSATION.id}`).click()
    await expect(page.getByTestId('conversation-page')).toBeVisible()
    await expect(page.getByTestId('messages-empty')).toBeVisible()
  })

  test('edge: only last 5 conversations are kept per project', async ({ page }) => {
    const newConversationId = 'conv-new-new-new-new-newnewnewnewnew'
    await page.evaluate(
      ({ projectId, datasourceId }) => {
        const conversations = Array.from({ length: 5 }, (_, index) => ({
          id: `conv-old-${index}`,
          projectId,
          datasourceId,
          title: `Conversation ${index}`,
          createdAt: new Date(2025, 0, index + 1).toISOString(),
          lastAccessedAt: new Date(2025, 0, index + 1).toISOString(),
        }))
        localStorage.setItem('cbi_conversations', JSON.stringify(conversations))
      },
      { projectId: MOCK_PROJECT.id, datasourceId: MOCK_DATASOURCE.id },
    )
    await page.reload()

    await page.route('**/api/v1/projects/**/conversations', async (route) => {
      if (route.request().method() === 'POST') {
        return route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            ...MOCK_CONVERSATION,
            id: newConversationId,
            title: 'Newest conversation',
            created_at: new Date(2025, 5, 1).toISOString(),
          }),
        })
      }
      return route.continue()
    })
    await page.route(`**/api/v1/conversations/${newConversationId}`, async (route) => {
      if (route.request().method() === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...MOCK_CONVERSATION,
            id: newConversationId,
            title: 'Newest conversation',
          }),
        })
      }
      return route.continue()
    })
    await page.route(`**/api/v1/conversations/${newConversationId}/messages`, async (route) => {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      })
    })

    await page.getByTestId(`start-conversation-${MOCK_DATASOURCE.id}`).click()
    await page.getByRole('link', { name: '← Back to project' }).click()

    await expect(page.getByTestId('conversation-list').locator('li')).toHaveCount(5)
    await expect(page.getByTestId('conversation-link-conv-old-0')).toHaveCount(0)
    await expect(page.getByTestId(`conversation-link-${newConversationId}`)).toBeVisible()
  })

  test('positive: send message and render query result with chart', async ({ page }) => {
    await page.goto(`/projects/${MOCK_PROJECT.id}/conversations/${MOCK_CONVERSATION.id}`)
    await page.getByTestId('message-input').fill('Show monthly revenue for 2025')
    await page.getByTestId('message-submit').click()

    await expect(page.getByTestId('query-result')).toBeVisible()
    await expect(page.getByTestId('viz-title')).toHaveText(MOCK_QUERY_RESPONSE.visualization!.title!)
    await expect(page.getByTestId('chart-bar')).toBeVisible()
    await expect(page.getByTestId('follow-up-questions')).toBeVisible()
    await expect(page.getByTestId('generated-query')).toContainText('SELECT')
  })

  test('positive: clarification response shows questions', async ({ page }) => {
    await page.goto(`/projects/${MOCK_PROJECT.id}/conversations/${MOCK_CONVERSATION.id}`)
    await page.getByTestId('message-input').fill('Please clarify the metrics')
    await page.getByTestId('message-submit').click()

    await expect(page.getByTestId('clarification-response')).toBeVisible()
    await expect(page.getByTestId('clarification-question')).toHaveCount(2)
  })

  test('edge: clicking clarification question fills input', async ({ page }) => {
    await page.goto(`/projects/${MOCK_PROJECT.id}/conversations/${MOCK_CONVERSATION.id}`)
    await page.getByTestId('message-input').fill('clarify please')
    await page.getByTestId('message-submit').click()

    await page.getByTestId('clarification-question').first().click()
    await expect(page.getByTestId('message-input')).not.toHaveValue('')
  })

  test('negative: query execution error is displayed', async ({ page }) => {
    await page.goto(`/projects/${MOCK_PROJECT.id}/conversations/${MOCK_CONVERSATION.id}`)
    await page.getByTestId('message-input').fill('trigger error query')
    await page.getByTestId('message-submit').click()

    await expect(page.getByTestId('query-error')).toBeVisible()
    await expect(page.getByTestId('query-error')).toContainText('does not exist')
  })

  test('edge: send button disabled for empty input', async ({ page }) => {
    await page.goto(`/projects/${MOCK_PROJECT.id}/conversations/${MOCK_CONVERSATION.id}`)
    await expect(page.getByTestId('message-submit')).toBeDisabled()
    await page.getByTestId('message-input').fill('   ')
    await expect(page.getByTestId('message-submit')).toBeDisabled()
  })

  test('negative: message send API failure shows error', async ({ page }) => {
    await loginAsMockUser(page)
    await page.goto(`/projects/${MOCK_PROJECT.id}/conversations/${MOCK_CONVERSATION.id}`)
    await expect(page.getByTestId('conversation-page')).toBeVisible()

    await page.route('**/api/v1/conversations/**/messages', (route) => {
      if (route.request().method() === 'POST') {
        return route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Rate limit exceeded' }),
        })
      }
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      })
    })
    await page.getByTestId('message-input').fill('Show sales data')
    await page.getByTestId('message-submit').click()

    await expect(page.getByTestId('conversation-error')).toContainText('Rate limit exceeded')
  })
})
