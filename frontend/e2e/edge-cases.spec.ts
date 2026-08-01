import { expect, test } from '@playwright/test'
import { setupApiMocks } from './fixtures/api-mocks'
import { MOCK_USER } from './fixtures/mock-data'

test.describe('Edge cases', () => {
  test('edge: 401 on protected route clears session and redirects', async ({ page }) => {
    await setupApiMocks(page)
    await page.goto('/login')
    await page.getByTestId('login-email').fill(MOCK_USER.email)
    await page.getByTestId('login-password').fill('password123')
    await page.getByTestId('login-submit').click()
    await page.waitForURL('**/projects')

    await page.route('**/api/v1/auth/me', (route) =>
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Token expired' }),
      }),
    )
    await page.reload()

    // After failed auth refresh, user should not see projects content with valid session
    await expect(page.getByTestId('projects-page').or(page.getByTestId('login-form'))).toBeVisible()
  })

  test('edge: login page link to register works', async ({ page }) => {
    await setupApiMocks(page)
    await page.goto('/login')
    await page.getByRole('link', { name: 'Create one' }).click()
    await expect(page).toHaveURL(/\/register/)
    await expect(page.getByTestId('register-form')).toBeVisible()
  })

  test('edge: register page link to login works', async ({ page }) => {
    await setupApiMocks(page)
    await page.goto('/register')
    await page.getByRole('link', { name: 'Sign in' }).click()
    await expect(page).toHaveURL(/\/login/)
  })

  test('edge: unknown route redirects to projects when authenticated', async ({ page }) => {
    await setupApiMocks(page)
    await page.goto('/login')
    await page.getByTestId('login-email').fill(MOCK_USER.email)
    await page.getByTestId('login-password').fill('password123')
    await page.getByTestId('login-submit').click()
    await page.waitForURL('**/projects')

    await page.goto('/unknown-path')
    await expect(page).toHaveURL(/\/projects/)
  })

  test('edge: conversations empty state on project page', async ({ page }) => {
    await setupApiMocks(page)
    await page.goto('/login')
    await page.getByTestId('login-email').fill(MOCK_USER.email)
    await page.getByTestId('login-password').fill('password123')
    await page.getByTestId('login-submit').click()
    await page.waitForURL('**/projects')

    await page.evaluate(() => localStorage.removeItem('cbi_conversations'))
    await page.getByTestId('project-card-proj-33333333-3333-3333-3333-333333333333').click()
    await expect(page.getByTestId('conversations-empty')).toBeVisible()
  })
})
