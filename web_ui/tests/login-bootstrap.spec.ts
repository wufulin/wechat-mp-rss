import { expect, test } from '@playwright/test'
import { readFileSync } from 'node:fs'

const packageMetadata = JSON.parse(
  readFileSync(new URL('../package.json', import.meta.url), 'utf-8')
) as { version: string }

test('login page does not load dashboard or chart modules', async ({ page }) => {
  const requestedPaths: string[] = []

  page.on('request', request => {
    requestedPaths.push(new URL(request.url()).pathname)
  })

  await page.goto('/login')

  await expect(page.getByRole('heading', { name: '欢迎回来' })).toBeVisible()
  await expect(
    page.getByText(`Version ${packageMetadata.version}`, { exact: true })
  ).toBeVisible()
  expect(
    requestedPaths.some(path => path.includes('/src/views/Dashboard.tsx'))
  ).toBe(false)
  expect(
    requestedPaths.some(path => path.includes('@visactor'))
  ).toBe(false)
})
