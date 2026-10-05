// Browser checks against the disposable localhost ABS only; never saves matches.
const fs = require('node:fs/promises')
const path = require('node:path')
const assert = require('node:assert/strict')

async function main() {
  const contextPath = process.argv[2]
  assert.ok(contextPath && path.basename(contextPath) === 'context.json')
  const config = JSON.parse(await fs.readFile(contextPath, 'utf8'))
  assert.match(config.base, /^http:\/\/127\.0\.0\.1:\d+$/)
  const { chromium } = require(process.env.SPIKE_PLAYWRIGHT_PACKAGE || 'playwright')
  const executablePath = process.env.SPIKE_BROWSER_EXECUTABLE || undefined
  const root = path.resolve(__dirname, '../..')
  const folder = path.join(root, 'docs/evidence/SPIKE-001')
  await fs.mkdir(folder, { recursive: true })
  const stamp = new Date().toISOString().replace(/[:.]/g, '')
  const checks = []
  const writes = []
  let browser
  let stage = 'launch'
  let outcome = 'Incomplete'
  let reason = null
  try {
    browser = await chromium.launch({ headless: true, executablePath })
    const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } })
    page.setDefaultTimeout(15000)
    // ABS defaults this UI to Google Books; prevent any unrelated provider lookup.
    await page.route('**/api/search/books?*', async route => {
      const url = new URL(route.request().url())
      if (url.searchParams.get('provider') !== config.provider_slug) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: '[]' })
      }
      return route.continue()
    })
    page.on('request', request => {
      const url = new URL(request.url())
      if (url.pathname.startsWith('/api/items/') && ['POST', 'PATCH', 'PUT', 'DELETE'].includes(request.method())) {
        writes.push({ method: request.method(), path_type: 'item_write' })
      }
    })
    stage = 'login'
    await page.goto(config.base + '/login', { waitUntil: 'networkidle' })
    const fields = page.locator('input')
    await fields.filter({ hasNot: page.locator('[type="password"]') }).first().fill(config.username).catch(async () => {
      await page.locator('input:not([type="password"])').first().fill(config.username)
    })
    await page.locator('input[type="password"]').fill(config.password)
    await page.getByRole('button', { name: /log ?in|sign ?in|submit/i }).click()
    await page.waitForURL(url => !url.pathname.includes('login'))
    stage = 'item'
    await page.goto(config.base + '/item/' + config.item_id, { waitUntil: 'networkidle' })
    stage = 'edit'
    await page.getByRole('button', { name: 'Edit', exact: true }).last().click()
    stage = 'match_tab'
    await page.getByText('Match', { exact: true }).last().click()
    const wrapper = page.locator('#match-wrapper')
    stage = 'choose_fixture_provider'
    await wrapper.getByText('Google Books', { exact: true }).first().click()
    await page.getByText('Synthetic Spike Provider', { exact: true }).last().click()
    await wrapper.getByRole('button', { name: 'Search', exact: true }).click()
    await wrapper.getByText(/Narrator A/).first().waitFor({ state: 'visible' })
    await wrapper.getByText(/Narrator B/).first().waitFor({ state: 'visible' })
    checks.push({ check: 'two_narrator_cards_visible', outcome: 'Pass' })
    await page.screenshot({ path: path.join(folder, `ui-cards-${stamp}.png`), fullPage: false })
    for (const narrator of ['Narrator A', 'Narrator B']) {
      stage = 'select_' + narrator.replace(/ /g, '_')
      await wrapper.getByText(new RegExp('Narrators?:.*' + narrator)).first().click()
      const selected = wrapper.locator(':scope > div.absolute')
      await selected.waitFor({ state: 'visible' })
      const selectedText = await selected.innerText()
      assert.ok(selectedText.includes(narrator))
      assert.ok(!selectedText.includes(narrator === 'Narrator A' ? 'Narrator B' : 'Narrator A'))
      checks.push({ check: 'select_' + narrator.replace(/ /g, '_'), outcome: 'Pass' })
      await page.screenshot({ path: path.join(folder, `ui-selection-${narrator.slice(-1)}-${stamp}.png`), fullPage: false })
      await selected.getByText('arrow_back', { exact: true }).click()
    }
    assert.equal(writes.length, 0)
    checks.push({ check: 'no_metadata_write_requests', outcome: 'Pass' })
    outcome = 'Pass'
  } catch (error) {
    reason = error.name
    // No exception text/trace/network headers or generated credentials in output.
    console.log('UI check incomplete at stage: ' + stage + ' (' + reason + ')')
    if (browser) {
      const pages = browser.contexts().flatMap(context => context.pages())
      if (pages[0]) {
        await pages[0].screenshot({ path: path.join(folder, `ui-incomplete-${stamp}.png`) }).catch(() => {})
      }
    }
  } finally {
    if (browser) await browser.close()
    const result = { captured_at_utc: new Date().toISOString(), classification: 'isolated_abs_rendered_ui',
      outcome, stage, stop_reason: reason, checks, item_write_request_count: writes.length,
      limitations: 'Synthetic editions and disposable ABS only; no live library or upstream API. Screenshots contain only invented fixture data.' }
    const target = path.join(folder, `ui-${stamp}.json`)
    await fs.writeFile(target, JSON.stringify(result, null, 2) + '\n', { flag: 'wx' })
    console.log('UI outcome: ' + outcome + '. Evidence: ' + path.relative(root, target))
  }
  process.exitCode = outcome === 'Pass' ? 0 : 1
}

main().catch(() => { console.error('UI fixture/configuration unavailable; no pass claimed.'); process.exitCode = 1 })
