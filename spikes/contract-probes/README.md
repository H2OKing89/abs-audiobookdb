# Initial contract probes

Development-only runner for [SPIKE-001](../../docs/spikes/SPIKE-001-abs-contract.md) and [SPIKE-002](../../docs/spikes/SPIKE-002-audiobookdb-contract.md). Gate A review: [readiness record](../../docs/reviews/gate-a-2026-10-05.md). This experiment is separate from the future adapter.

Run from the repository root on Linux/macOS with Python 3.10 or later (Unix signals enforce the total request deadline):

```sh
python3 spikes/contract-probes/probe.py self-check
python3 spikes/contract-probes/probe.py abs
python3 spikes/contract-probes/probe.py audiobookdb
```

The runner reads `.env` without executing shell code. `AUDIOBOOKSHELF_HOST` must use HTTPS. `AUDIOBOOKSHELF_API_FILE` and `AUDIOBOOKDB_API_FILE` name local key files; when empty, the runner explicitly records its use of existing `secrets/audiobookshelf_api_key` and `secrets/audiobookdb_api_key`. Key values stay in memory and request headers. No credential file is created or modified.

For keyed AudiobookDB reads, supply `--user-agent 'abs-audiobookdb-spikes/0.1 (your actual contact)'` to meet the documented contact requirement. The default identifies the application and local owner but does not invent a contact address; it was accepted in the selected EVD-005 requests; that observation does not change the documented contact requirement.

ABS checks are GET `/status` and authenticated GET `/api/libraries`; the installed version is taken from `serverVersion` when present. AudiobookDB checks public OpenAPI, read-only POST `/api/search`, one book, an author-filtered search derived from its observed relationships, up to two releases, roles, external categories and known/unknown ASIN resolution. ISBN category flags and runtime unit consistency are summarized without catalog values. Redirects and other POST requests are rejected. TLS certificates are verified. Requests are sequential, spaced at least 250 ms apart, bounded to ten seconds and 1 MiB each (2 MiB for the schema), with no retries. The API budget is ten requests/20 documented cost units; the public schema fetch is separate.

Evidence files under `docs/evidence/SPIKE-001/` and `SPIKE-002/` contain timestamps, status codes, field names/types, response sizes and safe header names. API bodies, hostnames, keys, account values and catalog text are excluded. Each run creates a new file and preserves failures. Exit code 1 means an incomplete or blocked probe.

A successful runner remains partial evidence: it does not measure ABS provider requests, deadlines or UI selection; it does not prove ISBN edition resolution, filter behavior across all edge fixtures, edition mapping, isolation or deployment. Do not mark a full verification check passed from this runner alone.

Normally run the probes directly. Earlier restricted-sandbox DNS failures were worked around by SSH into the same development host; that was a different execution context, not a different machine. If that restriction recurs and existing SSH access is available, use your own host and checkout path:

```sh
ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=yes user@development-host python3 /path/to/abs-audiobookdb/spikes/contract-probes/probe.py all
```

Verify that the server has the same runner first using `sha256sum` locally and over SSH. Each execution records the runner hash and whether it ran in an SSH session. The server must already contain the repository and local credentials; this workflow does not transfer or change them.
