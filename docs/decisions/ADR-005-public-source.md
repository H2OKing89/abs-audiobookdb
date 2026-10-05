# Public source repository and MIT license

Status: Accepted  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## ID and status: ADR-005 / Accepted

Public GitHub source preparation authorized by the owner.

## Context and linked requirements

The adapter passed private MVP acceptance (EVD-017). Q-008 previously deferred
public distribution; the user now requests GitHub preparation, chooses public
visibility, identifies H2OKing89 and selects MIT.

## Decision question

What can be published, under which license, and how is the repository checked?

## Options and tradeoffs

Private/unlicensed storage was the earlier default. Public MIT source supports
contributions and reuse. API accounts, keys and metadata dumps are not part of
the adapter source or license grant.

## Decision and rationale

Prepare `H2OKing89/abs-audiobookdb` as a public MIT source repository with
offline CI, an example configuration, contributor/PR guidance and generic
installation instructions. Publish invented fixtures and sanitized evidence;
preserve historical failures. Runtime/API behavior remains baseline 1.0.

## Evidence and source versions

Explicit user choices on 2026-10-05; local Git/history privacy review and
repository checks recorded in EVD-018. Official actions/checkout and
actions/setup-go tags verified and pinned to commit SHAs in CI.

## Consequences and risks

MIT covers project-authored source and documentation; it does not license
upstream services/data or ABS assets. Operators use their own upstream account
and follow its current API requirements/terms. Provider approval or legal
compatibility is not represented. No metadata archive is distributed.

## Affected documents and tests

LICENSE, README, CONTRIBUTING, examples, GitHub workflow/templates and current
publication dispositions. Git preparation does not permanently deploy Unraid
or configure the live ABS library.

## Reviewer and date

Owner selections: public / H2OKing89 / MIT, 2026-10-05. Codex prepared local
repository changes and checks; remote publication is a separate action.

## Supersedes / superseded by

Supersedes Q-008's blanket source-publication deferral for this authorized
scope. Historical private spike/review/evidence records stay unchanged.
