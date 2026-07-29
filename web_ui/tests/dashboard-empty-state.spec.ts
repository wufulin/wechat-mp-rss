import { expect, type Page, test } from '@playwright/test'

const mockDashboardApis = async (page: Page) => {
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname

    if (path.endsWith('/wx/dashboard/stats')) {
      await route.fulfill({
        json: {
          code: 0,
          data: {
            stats: {
              totalArticles: 0,
              totalSources: 1,
              todayArticles: 0,
              weekArticles: 0
            },
            sourceStats: [
              {
                mp_id: 'source-1',
                mp_name: '诺万资产',
                article_count: 0,
                percentage: 0
              }
            ],
            keywordStats: [],
            trendData: [],
            keywordTrendData: []
          }
        }
      })
      return
    }

    if (path.endsWith('/wx/user')) {
      await route.fulfill({
        json: {
          code: 0,
          data: {
            username: 'admin',
            nickname: 'admin',
            email: '',
            avatar: '',
            role: 'admin',
            is_active: true,
            created_at: ''
          }
        }
      })
      return
    }

    if (path.endsWith('/wx/sys/info')) {
      await route.fulfill({ json: { code: 0, data: { wx: { login: false } } } })
      return
    }

    await route.fulfill({ json: { code: 0, data: {} } })
  })
}

test.beforeEach(async ({ page }) => {
  await mockDashboardApis(page)
  await page.addInitScript(() => {
    localStorage.setItem('token', 'mock-token')
  })
})

test('new users see no watermark and zero-count sources render as no data', async ({ page }) => {
  await page.goto('/dashboard')

  const sourceDistributionCard = page
    .getByText('来源分布', { exact: true })
    .locator('..')
    .locator('..')

  await expect(sourceDistributionCard.getByText('暂无数据', { exact: true })).toBeVisible()
  await expect(page.getByText(`微信公众号热度分析系统 · ${new Date().getFullYear()}`, { exact: true })).toHaveCount(0)
})

test('users can still explicitly enable the watermark', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('app_settings', JSON.stringify({
      watermarkEnabled: true,
      darkMode: false
    }))
  })

  await page.goto('/dashboard')

  await expect(page.getByText(`微信公众号热度分析系统 · ${new Date().getFullYear()}`, { exact: true })).toHaveCount(150)
})
