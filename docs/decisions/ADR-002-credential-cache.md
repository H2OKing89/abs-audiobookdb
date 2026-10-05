# Authenticated bounded result caching

Status: Finalized for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## ID and status: ADR-002 / Accepted for private MVP

Replace the synthetic validation hypothesis with the verified real endpoint.

## Context and linked requirements

REQ-008/009; Q-005/006; cache hits must not bypass credential rejection.

## Decision question

How can cache reuse remain authorized and bounded?

## Options and tradeoffs

TTL-only authorization is stale. Removing all caching avoids reuse but repeats expansion. Fresh authenticated session checks permit short-lived result reuse at one cost unit per warm request.

## Decision and rationale

GET `/auth/session` before every cache read. Partition complete mapped result bytes by nonlogged credential fingerprint and canonical query. Cache TTL 60 seconds, at most 64 entries and four MiB counted payload-plus-key bytes; one MiB/entry. Purge on any observed 401/403. Invalidation generation suppresses writes begun before a rejection. Sweep expired entries periodically and on access. Cache successful empty searches at the same TTL; never cache failures. Cross-request singleflight is deferred to keep cancellation/admission simple.

## Evidence and source versions

EVD-015 real auth and measured warm reuse; EVD-016 seven synthetic race/budget/cache tests. EVD-012 remains evidence of an earlier alternative with synthetic /validate and shared flights.

## Consequences and risks

Warm auth consumes quota and must obey the same global pace/deadline. An already authorized request may finish around a concurrent revocation; later requests revalidate. Cache byte limits do not equal total process RSS. No persisted catalog cache.

## Affected documents and tests

Architecture; SPIKE-004/006; VER-006–008; VAL-002/003. Production tests must exercise actual client/cache and invalidation while work is active.

## Reviewer and date

Codex technical review under user finalization instruction, 2026-10-05.

## Supersedes / superseded by

Revises this record’s earlier proposed synthetic-validation policy; historical artifacts preserved.
