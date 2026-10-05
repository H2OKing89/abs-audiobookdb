// Exercise pinned ABS source with synthetic dependencies, without touching ABS.
const fs = require('node:fs/promises')
const path = require('node:path')
const vm = require('node:vm')
const crypto = require('node:crypto')
const assert = require('node:assert/strict')

const commit = '3563d49424d50170324de9236a24c591b6d965e9'
const expectedHash = '46c59c6f6c8758af29492bbb5eaeab78585d1d95c1fd9634782411bb5e7dcb4e'
const sourceUrl = `https://raw.githubusercontent.com/advplyr/audiobookshelf/${commit}/server/providers/CustomProviderAdapter.js`
const checked = []

async function main() {
  const response = await fetch(sourceUrl, { signal: AbortSignal.timeout(10000), redirect: 'error' })
  if (!response.ok) throw new Error('source_fetch_failed')
  const bytes = Buffer.from(await response.arrayBuffer())
  assert.ok(bytes.length < 524288, 'source_size_limit')
  const sourceHash = crypto.createHash('sha256').update(bytes).digest('hex')
  assert.equal(sourceHash, expectedHash, 'source_hash_mismatch')
  const provider = { url: 'https://provider.invalid', authHeaderValue: 'SYNTHETIC-SENTINEL' }
  let captured
  let payload = { matches: [] }
  let rejectRequest = false
  const dependencies = {
    axios: { default: { get: async (url, options) => {
      captured = { url, options }
      if (rejectRequest) throw new Error('synthetic_transport_failure')
      return { data: payload }
    } } },
    '../Database': { customMetadataProviderModel: { findByPk: async () => provider } },
    '../Logger': { debug() {}, error() {} },
    '../utils/htmlSanitizer': { sanitize: value => value }
  }
  const sandbox = { module: { exports: {} }, URLSearchParams,
    require: name => {
      if (!(name in dependencies)) throw new Error('unexpected_dependency')
      return dependencies[name]
    } }
  vm.runInNewContext(bytes.toString('utf8'), sandbox, { timeout: 1000 })
  const adapter = new sandbox.module.exports()
  const search = (isbn = '9780000000002', timeout) => adapter.search('Synthetic Title', 'Synthetic Author', isbn, 'custom-synthetic', 'book', timeout)
  await search()
  const params = new URL(captured.url).searchParams
  assert.equal(params.get('query'), 'Synthetic Title')
  assert.equal(params.get('author'), 'Synthetic Author')
  assert.equal(params.get('isbn'), '9780000000002')
  assert.equal(params.get('mediaType'), 'book')
  assert.equal(params.has('asin'), false)
  assert.equal(captured.options.headers.Authorization, provider.authHeaderValue)
  assert.equal(captured.options.timeout, 10000)
  checked.push('request_parameters_raw_authorization_default_timeout')
  await search('', 250)
  assert.equal(new URL(captured.url).searchParams.has('isbn'), false)
  assert.equal(captured.options.timeout, 250)
  checked.push('optional_isbn_and_timeout_override')
  provider.authHeaderValue = ''
  await search()
  assert.equal(captured.options.headers, undefined)
  checked.push('empty_auth_omits_header')
  payload = { matches: [
    { title: 'Synthetic Edition', narrator: 'Narrator A', publishedYear: 2026,
      genres: [' Sample ', 'Sample'], duration: '120',
      series: [{ series: 'Synthetic Series', sequence: 0 }, { series: 'Synthetic Series', sequence: '0.5' }],
      releaseId: 'synthetic-a' },
    { title: 'Synthetic Edition', narrator: 'Narrator B', author: ['Author A', 'Author B'],
      series: [{ series: 'Synthetic Series', sequence: '0' }], releaseId: 'synthetic-b' }
  ] }
  const normalized = JSON.parse(JSON.stringify(await search()))
  assert.equal(normalized.length, 2)
  assert.notEqual(normalized[0].narrator, normalized[1].narrator)
  assert.equal(normalized[0].publishedYear, '2026')
  assert.equal(normalized[0].duration, 120)
  assert.deepEqual(normalized[0].genres, ['Sample'])
  assert.equal(normalized[1].author, 'Author A,Author B')
  assert.equal('releaseId' in normalized[0], false)
  assert.equal('sequence' in normalized[0].series[0], false)
  assert.equal(normalized[0].series[1].sequence, '0.5')
  assert.equal(normalized[1].series[0].sequence, '0')
  checked.push('two_narrator_variants_preserved_and_fields_normalized')
  checked.push('numeric_zero_sequence_dropped_string_zero_preserved')
  checked.push('extra_release_id_removed')
  payload = {}
  await assert.rejects(search(), /malformed response/)
  checked.push('successful_malformed_envelope_throws')
  rejectRequest = true
  assert.deepEqual(JSON.parse(JSON.stringify(await search())), [])
  checked.push('transport_or_http_rejection_becomes_empty_results')
  const root = path.resolve(__dirname, '../..')
  const folder = path.join(root, 'docs/evidence/SPIKE-001')
  await fs.mkdir(folder, { recursive: true })
  const timestamp = new Date().toISOString().replace(/[:.]/g, '')
  const target = path.join(folder, `source-check-${timestamp}.json`)
  const result = { captured_at_utc: new Date().toISOString(), classification: 'pinned_source_with_synthetic_dependencies',
    source_url: sourceUrl, source_commit: commit, source_sha256: sourceHash,
    node_version: process.version, outcome: 'Pass', checks: checked,
    limitations: 'Database, Axios, logging and HTML sanitizer are stubbed. No HTTP capture, measured timeout, running ABS instance or UI validation. Sentinel values are excluded from output.' }
  await fs.writeFile(target, JSON.stringify(result, null, 2) + '\n', { flag: 'wx' })
  console.log(`Pinned ABS source checks passed: ${checked.length}. Evidence: ${path.relative(root, target)}`)
}

main().catch(() => {
  console.error('Pinned source check failed; no result pass was recorded.')
  process.exitCode = 1
})
