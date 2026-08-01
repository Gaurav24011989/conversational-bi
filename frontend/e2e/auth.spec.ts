import { expect, test } from '@playwright/test'
import { setupApiMocks } from './fixtures/api-mocks'
import { MOCK_USER } from './fixtures/mock-data'

test.describe('Authentication', () => {
  test('positive: successful login redirects to projects', async ({ page }) => {
    await setupApiMocks(page)
    await page.goto('/login')
    await page.getByTestId('login-email').fill(MOCK_USER.email)
    await page.getByTestId('login-password').fill('password123')
    await page.getByTestId('login-submit').click()

    await expect(page).toHaveURL(/\/projects/)
    await expect(page.getByTestId('projects-page')).toBeVisible()
    await expect(page.getByTestId('user-email')).toHaveText(MOCK_USER.email)
  })

  test('negative: invalid credentials show error', async ({ page }) => {
    await setupApiMocks(page, { loginFails: true })
    await page.goto('/login')
    await page.getByTestId('login-email').fill('wrong@example.com')
    await page.getByTestId('login-password').fill('badpassword')
    await page.getByTestId('login-submit').click()

    await expect(page.getByTestId('login-error')).toContainText('Invalid credentials')
    await expect(page).toHaveURL(/\/login/)
  })

  test('positive: successful registration redirects to projects', async ({ page }) => {
    await setupApiMocks(page)
    await page.goto('/register')
    await page.getByTestId('register-full-name').fill('New User')
    await page.getByTestId('register-email').fill('new@example.com')
    await page.getByTestId('register-password').fill('securepass')
    await page.getByTestId('register-org-name').fill('Acme Corp')
    await expect(page.getByTestId('register-org-slug')).toHaveValue('acme-corp')
    await page.getByTestId('register-submit').click()

    await expect(page).toHaveURL(/\/projects/)
    await expect(page.getByTestId('projects-page')).toBeVisible()
  })

  test('negative: duplicate org slug shows error', async ({ page }) => {
    await setupApiMocks(page, { registerFails: true })
    await page.goto('/register')
    await page.getByTestId('register-email').fill('dup@example.com')
    await page.getByTestId('register-password').fill('securepass')
    await page.getByTestId('register-org-name').fill('Acme')
    await page.getByTestId('register-org-slug').fill('acme')
    await page.getByTestId('register-submit').click()

    await expect(page.getByTestId('register-error')).toContainText('Organization slug already exists')
  })

  test('edge: unauthenticated user is redirected to login', async ({ page }) => {
    await setupApiMocks(page)
    await page.goto('/projects')
    await expect(page).toHaveURL(/\/login/)
  })

  test('edge: logout clears session and redirects', async ({ page }) => {
    await setupApiMocks(page)
    await page.goto('/login')
    await page.getByTestId('login-email').fill(MOCK_USER.email)
    await page.getByTestId('login-password').fill('password123')
    await page.getByTestId('login-submit').click()
    await page.waitForURL('**/projects')

    await page.getByTestId('logout-button').click()
    await page.goto('/projects')
    await expect(page).toHaveURL(/\/login/)
  })
})
