# Pinned ABS source check

Plan: [SPIKE-001](../../docs/spikes/SPIKE-001-abs-contract.md). Run with Node.js 18 or later:

```sh
node spikes/SPIKE-001/source-contract-check.js
```

The script downloads only `CustomProviderAdapter.js` from the pinned ABS 2.37.1 commit, verifies its expected SHA-256, and executes that source with synthetic Axios/database/logging/HTML-sanitizer dependencies. It checks query/header construction, timeout configuration, response normalization and error handling. It never connects to ABS, reads credentials or modifies provider settings.

Results are saved under `docs/evidence/SPIKE-001/source-check-*.json`. This is a source-component experiment, not live provider capture or UI validation. HTML sanitization and real Axios timing are outside its scope. The source-review evidence record links the latest results.

## Disposable live integration and browser

```sh
python3 spikes/SPIKE-001/live_experiment.py --keep-for-ui
node spikes/SPIKE-001/ui_experiment.cjs /tmp/abs-spike-RUN/context.json
```

Use the context path printed by the first command; it contains generated test credentials and stays in temporary storage. The runner creates a labeled dedicated Docker bridge network, a digest-pinned ABS 2.37.1 container and a synthetic provider container. Ports bind to loopback; generated audio/configuration are under `/tmp`. No `.env`, real library, real provider or real credentials are used. The generated matches come from the synthetic SPIKE-003 mapper.

The integration checks actual request/auth forwarding, two matches, 1/5/11-second delays, six provider error statuses and a malformed successful envelope, replacement-key forwarding and previous-key rejection. Thirteen API searches fit a 17-second synthetic delay budget. The browser intercepts default-provider searches and is allowed at most four fixture searches per run and selects both narrator cards without saving metadata. Playwright/browser package and executable can be selected using `SPIKE_PLAYWRIGHT_PACKAGE` and `SPIKE_BROWSER_EXECUTABLE`; current defaults use the local temporary package and existing cached Chromium. No browser download is required if that cache exists.

After browser completion, send a line to the waiting first process; it removes only its own two containers, network and temporary data, and writes an integration summary. API outcomes, browser outcomes and screenshots are separate evidence. A failed run remains recorded; cleanup failures are not silently marked successful. Without `--keep-for-ui`, API checks clean up immediately.
