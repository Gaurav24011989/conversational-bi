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
    await expect(page.getByTestId('conversation-list')).toBeVisible()
    await page.getByTestId(`conversation-link-${MOCK_CONVERSATION.id}`).click()

    await expect(page).toHaveURL(
      new RegExp(`/projects/${MOCK_PROJECT.id}/conversations/${MOCK_CONVERSATION.id}`),
    )
    await expect(page.getByTestId('conversation-page')).toBeVisible()
    await expect(page.getByTestId('messages-empty')).toBeVisible()
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
