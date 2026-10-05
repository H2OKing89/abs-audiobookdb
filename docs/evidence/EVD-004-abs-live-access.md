# ABS live development access

Status: Partial  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID: EVD-004

SPIKE-001 readiness subcheck passed; full provider contract remains pending.

## Source URL or fixture provenance

Configured developer ABS host and key-file path from ignored `.env`; private host and key omitted. No fallback credential path was needed.

## Captured date and environment

2026-10-05T17:04:01 UTC initial successful run; 17:06:41 UTC version follow-up. Python 3.14.4 on the development server through existing SSH access. A local workspace retry at 17:02:40 still failed DNS; the user's successful host lookup does not establish workspace network access.

## Version, commit or content hash

Installed ABS reports `serverVersion` 2.37.1. Final runner SHA-256: `fb9c680b56aa91289062992904639e5a71e12e5ec048db3851758a63b5ce597e`. The locally edited and remotely executed runner hashes were compared and matched before execution.

## Method and reproduction steps

Run the SSH command in [the probe README](../../spikes/contract-probes/README.md). Each run attempted exactly two GETs: `/status` and Bearer-authenticated `/api/libraries`, with TLS verification, no redirects and no retries. Initial version extraction looked for `version`; follow-up corrected it to the observed `serverVersion` field. No other ABS calls occurred.

## Sanitized artifact path

- [Local DNS retry](SPIKE-001/probe-20261005T170240190228Z.json).
- [Initial successful access](SPIKE-001/probe-20261005T170401029257Z.json).
- [Version follow-up](SPIKE-001/probe-20261005T170641207974Z.json).

## Claims supported and limitations

Both GETs returned HTTP 200 with JSON; configured development credentials were accepted for the read. The follow-up reports ABS 2.37.1. This establishes development API access only. The ABS token is unrelated to the adapter's upstream AudiobookDB credential forwarding. No provider request was captured; authorization forwarding, response acceptance, deadline, installed-version source comparison and UI edition selection remain pending.

## Observed outcome

Readiness subcheck Pass; full SPIKE-001 Partial. Final GET timings were 9 ms and 20 ms, measured from the development server; these are not provider end-to-end latency measurements.

## Synthetic or live classification

Live read-only ABS responses; no synthetic runtime results substituted.

## Sanitization and redistribution notes

Only JSON shapes, version and transport metadata saved. Library names, filesystem paths, IDs, configuration values, private host and credentials are excluded. No ABS library/provider configuration or metadata was modified.
