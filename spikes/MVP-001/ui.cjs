const fs = require('node:fs/promises')
const assert = require('node:assert/strict')
const path = require('node:path')

async function main() {
  const target = process.argv[2]
  assert.ok(target && path.basename(target) === 'context.json')
  const config = JSON.parse(await fs.readFile(target, 'utf8'))
  assert.match(config.base, /^http:\/\/127\.0\.0\.1:\d+$/)
  const { chromium } = require(process.env.SPIKE_PLAYWRIGHT_PACKAGE || 'playwright')
  const browser = await chromium.launch({ headless: true, executablePath: process.env.SPIKE_BROWSER_EXECUTABLE || undefined })
  const checks = []
  let writes = 0
  try {
    const page = await browser.newPage()
    page.setDefaultTimeout(15000)
    await page.route('**/api/search/books?*', route => {
      if (new URL(route.request().url()).searchParams.get('provider') !== config.provider_slug) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: '[]' })
      }
      return route.continue()
    })
    page.on('request', req => { if (new URL(req.url()).pathname.startsWith('/api/items/') && ['POST','PUT','PATCH','DELETE'].includes(req.method())) writes++ })
    await page.goto(config.base + '/login', { waitUntil: 'networkidle' })
    await page.locator('input:not([type="password"])').first().fill(config.username)
    await page.locator('input[type="password"]').fill(config.password)
    await page.getByRole('button', { name: /log ?in|sign ?in|submit/i }).click()
    await page.waitForURL(url => !url.pathname.includes('login'))
    await page.goto(config.base + '/item/' + config.item_id, { waitUntil: 'networkidle' })
    await page.getByRole('button', { name: 'Edit', exact: true }).last().click()
    await page.getByText('Match', { exact: true }).last().click()
    const wrapper = page.locator('#match-wrapper')
    await wrapper.getByText('Google Books', { exact: true }).first().click()
    await page.getByText('Synthetic MVP Provider', { exact: true }).last().click()
    await wrapper.getByRole('button', { name: 'Search', exact: true }).click()
    await wrapper.getByText(/Narrator B/).first().waitFor({ state: 'visible' })
    for (const name of ['Narrator A', 'Narrator B', 'Full Cast']) {
      await wrapper.getByText(new RegExp('Narrators?:.*' + name)).first().click()
      const selected = wrapper.locator(':scope > div.absolute')
      await selected.waitFor({ state: 'visible' })
      assert.ok((await selected.innerText()).includes(name))
      await selected.getByText('arrow_back', { exact: true }).click()
      checks.push({ check: 'ui_select_' + name.replaceAll(' ', '_'), outcome: 'Pass' })
    }
    // ABS 2.37.1 cards omit language/subtitle. Select the second recording
    // of Narrator A; the selection form exposes its French language.
    await wrapper.getByText(/Narrators?:.*Narrator A/).nth(1).click()
    const selected = wrapper.locator(':scope > div.absolute')
    await selected.waitFor({ state: 'visible' })
    const inputs = await selected.locator('input').evaluateAll(nodes => nodes.map(node => node.value))
    assert.ok(inputs.includes('French'))
    assert.equal(writes, 0)
    checks.push({ check: 'ui_same_narrator_french_release_language', outcome: 'Pass' })
    checks.push({ check: 'ui_no_item_writes_or_default_provider_searches', outcome: 'Pass' })
    console.log(JSON.stringify({ outcome: 'Pass', checks }))
  } finally { await browser.close() }
}
main().catch(() => { console.log(JSON.stringify({ outcome: 'Incomplete', checks: [] })); process.exitCode = 1 })
