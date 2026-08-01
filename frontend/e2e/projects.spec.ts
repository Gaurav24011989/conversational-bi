import { expect, test } from '@playwright/test'
import { loginAsMockUser, setupApiMocks } from './fixtures/api-mocks'
import { MOCK_PROJECT, MOCK_PROJECT_2 } from './fixtures/mock-data'

test.describe('Projects', () => {
  test('positive: lists projects', async ({ page }) => {
    await loginAsMockUser(page)
    await expect(page.getByTestId('project-list')).toBeVisible()
    await expect(page.getByTestId(`project-card-${MOCK_PROJECT.id}`)).toContainText('Default Project')
    await expect(page.getByTestId(`project-card-${MOCK_PROJECT_2.id}`)).toContainText('Sales Analytics')
  })

  test('positive: creates a new project', async ({ page }) => {
    await loginAsMockUser(page)
    await page.getByTestId('new-project-button').click()
    await expect(page.getByTestId('new-project-form')).toBeVisible()
    await page.getByTestId('project-name-input').fill('Marketing Dashboard')
    await page.getByTestId('project-description-input').fill('Campaign metrics')
    await page.getByTestId('create-project-submit').click()

    await expect(page.getByText('Marketing Dashboard')).toBeVisible()
  })

  test('positive: navigates to project detail', async ({ page }) => {
    await loginAsMockUser(page)
    await page.getByTestId(`project-card-${MOCK_PROJECT.id}`).click()
    await expect(page).toHaveURL(new RegExp(`/projects/${MOCK_PROJECT.id}`))
    await expect(page.getByTestId('project-detail-page')).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Default Project' })).toBeVisible()
  })

  test('edge: empty project list shows empty state', async ({ page }) => {
    await setupApiMocks(page)
    await page.goto('/login')
    await page.getByTestId('login-email').fill('analyst@example.com')
    await page.getByTestId('login-password').fill('password123')
    await page.route('**/api/v1/orgs/**/projects', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    )
    await page.getByTestId('login-submit').click()
    await page.waitForURL('**/projects')

    await expect(page.getByTestId('projects-empty')).toBeVisible()
  })

  test('negative: API error displays alert', async ({ page }) => {
    await setupApiMocks(page)
    await page.goto('/login')
    await page.getByTestId('login-email').fill('analyst@example.com')
    await page.getByTestId('login-password').fill('password123')
    await page.getByTestId('login-submit').click()
    await page.waitForURL('**/projects')

    await page.route('**/api/v1/orgs/**/projects', (route) =>
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' }),
      }),
    )
    await page.reload()
    await expect(page.getByTestId('projects-error')).toContainText('Internal server error')
  })
})
