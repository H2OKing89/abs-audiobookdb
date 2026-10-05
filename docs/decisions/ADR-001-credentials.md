# Credential forwarding and configuration

Status: Finalized for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## ID and status: ADR-001 / Accepted for private MVP

Technical decision within the user’s instruction to finish planning; no external provider approval represented.

## Context and linked requirements

REQ-004/008; development ABS host/key in ignored `.env` are never adapter runtime inputs.

## Decision question

How does the adapter select and validate the caller’s upstream key?

## Options and tradeoffs

Header-only minimizes configuration; optional fallback supports a single-user installation. Anonymous access or a separate local-token mode would change the authentication contract and is deferred.

## Decision and rationale

Use incoming raw Authorization or case-insensitive Bearer normalization. Permit optional AUDIOBOOKDB_API_KEY fallback only when the Authorization header is absent. Malformed/rejected supplied credentials never fall back. No anonymous path. GET `/auth/session` with X-API-Key validates every search request before cache access. Retain no returned user profile; purge that credential’s cache on upstream 401/403. Require configurable operator contact in meaningful application/version User-Agent.

## Evidence and source versions

EVD-010 actual ABS raw forwarding/replacement; EVD-015 real `/auth/session` accepts configured key and rejects invalid/missing keys; OpenAPI 1.0.0 pinned hash.

## Consequences and risks

Every warm request costs one authenticated detail read. Revocation is detected when upstream rejects a subsequent request; no promise of zero-time rejection for already authorized work. Keys/profile/headers/raw queries never logged. Missing operator contact is a configuration error, not grounds to invent contact information.

## Affected documents and tests

Architecture, SPIKE-006, VAL-002, production credential/config tests.

## Reviewer and date

Codex technical review, 2026-10-05; user authorized this planning/finalization work with “do it.”

## Supersedes / superseded by

None; resolves previously reserved ADR-001.
