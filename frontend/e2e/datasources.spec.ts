import { expect, test } from '@playwright/test'
import { loginAsMockUser } from './fixtures/api-mocks'
import { MOCK_DATASOURCE, MOCK_PROJECT } from './fixtures/mock-data'

test.describe('Data sources', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsMockUser(page)
    await page.getByTestId(`project-card-${MOCK_PROJECT.id}`).click()
  })

  test('positive: lists datasources', async ({ page }) => {
    await expect(page.getByTestId('datasource-list')).toBeVisible()
    await expect(page.getByTestId(`datasource-${MOCK_DATASOURCE.id}`)).toContainText(
      'Production Postgres',
    )
    await expect(page.getByTestId(`datasource-${MOCK_DATASOURCE.id}`)).toContainText('postgresql')
  })

  test('positive: creates a datasource', async ({ page }) => {
    await page.getByTestId('new-datasource-button').click()
    await page.getByTestId('datasource-name').fill('Analytics DB')
    await page.getByTestId('datasource-type').selectOption('mysql')
    await page.getByTestId('datasource-host').fill('db.example.com')
    await page.getByTestId('datasource-port').fill('3306')
    await page.getByTestId('datasource-database').fill('analytics')
    await page.getByTestId('datasource-username').fill('reader')
    await page.getByTestId('datasource-password').fill('secret')
    await page.getByTestId('create-datasource-submit').click()

    await expect(page.getByText('Analytics DB')).toBeVisible()
  })

  test('positive: test connection shows success', async ({ page }) => {
    await page.getByTestId(`test-${MOCK_DATASOURCE.id}`).click()
    await expect(page.getByTestId('datasource-test-result')).toContainText('Connected')
  })

  test('positive: refresh schema shows confirmation', async ({ page }) => {
    await page.getByTestId(`refresh-schema-${MOCK_DATASOURCE.id}`).click()
    await expect(page.getByTestId('datasource-test-result')).toContainText('Schema refreshed')
  })

  test('edge: empty datasources shows empty state', async ({ page }) => {
    await page.route('**/api/v1/projects/**/datasources', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    )
    await page.reload()
    await expect(page.getByTestId('datasources-empty')).toBeVisible()
  })

  test('negative: datasource creation failure shows error', async ({ page }) => {
    await page.getByTestId('new-datasource-button').click()
    await page.route('**/api/v1/projects/**/datasources', (route) => {
      if (route.request().method() === 'POST') {
        return route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({ detail: "Permission 'configure_datasource' denied" }),
        })
      }
      return route.continue()
    })
    await page.getByTestId('datasource-name').fill('Blocked DS')
    await page.getByTestId('datasource-database').fill('test')
    await page.getByTestId('create-datasource-submit').click()

    await expect(page.getByTestId('project-error')).toContainText('configure_datasource')
  })
})
