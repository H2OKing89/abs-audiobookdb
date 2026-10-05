# ABS 2.37.1 source-component verification

Status: Partial  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID: EVD-006

SPIKE-001 pinned source inspection and synthetic component experiment.

## Source URL or fixture provenance

ABS v2.37.1 resolves to commit `3563d49424d50170324de9236a24c591b6d965e9`. Reviewed files:

- [CustomProviderAdapter.js](https://github.com/advplyr/audiobookshelf/blob/3563d49424d50170324de9236a24c591b6d965e9/server/providers/CustomProviderAdapter.js).
- [BookFinder.js](https://github.com/advplyr/audiobookshelf/blob/3563d49424d50170324de9236a24c591b6d965e9/server/finders/BookFinder.js).
- [SearchController.js](https://github.com/advplyr/audiobookshelf/blob/3563d49424d50170324de9236a24c591b6d965e9/server/controllers/SearchController.js).
- [BookMatchCard.vue](https://github.com/advplyr/audiobookshelf/blob/3563d49424d50170324de9236a24c591b6d965e9/client/components/cards/BookMatchCard.vue).

## Captured date and environment

2026-10-05 UTC; public source retrieved directly from this machine with networking enabled. No SSH was needed. Installed ABS version was reported separately in EVD-004; installed files have not been compared byte-for-byte with the tag.

## Version, commit or content hash

Adapter SHA-256: `46c59c6f6c8758af29492bbb5eaeab78585d1d95c1fd9634782411bb5e7dcb4e`.
BookFinder SHA-256: `fb5366ad2e0a4312ccd9f2d9fe2541aac7a0860d5f0b7078d6cf11431186a025`.
SearchController SHA-256: `6d100d390793512a5dc0a5941b033437726c5ed52436c584ae5995ba2eeac433`.
BookMatchCard SHA-256: `04e6f643848b37a5e0143c4ea9e170784acc934e0cc85694abc5bc49ccc9a28c`.

## Method and reproduction steps

Resolve the version tag with `git ls-remote`, fetch the commit-pinned files, and inspect provider/caller/UI paths. Run `node spikes/SPIKE-001/source-contract-check.js`; it independently fetches the adapter, verifies its hash and exercises it with synthetic Axios/database/logging/sanitizer dependencies. Eight check groups must pass; no production source was copied into the repository or changed.

## Sanitized artifact path

[Source-component result](SPIKE-001/source-check-2026-10-05T172350976Z.json). Synthetic sentinel credentials and match contents are excluded from saved output.

## Claims supported and limitations

The adapter constructs `/search` with mediaType/query and optional author/ISBN, sends the configured Authorization value unchanged, defaults to 10,000 ms, and preserves two narrator variants. It normalizes values and discards extra release-ID fields. Numeric series zero is lost; string zero/fractional sequences survive. Rejected HTTP/transport promises become empty results; malformed successful envelopes throw. These behaviors passed component checks; real timeout measurement and sanitizer behavior were not tested.

BookFinder also uses ten seconds and catches adapter exceptions as empty results. The interactive search controller supplies title/author but no ISBN/ASIN to BookFinder. The card displays narrator and converts duration minutes to seconds. These are source observations, not live capture or rendered UI results. Tag matching alone does not establish that the deployment contains unmodified source.

## Observed outcome

Eight source-component check groups Pass; full SPIKE-001 and VER-001 remain Partial. Actual request capture, measured deadline and UI acceptance remain pending.

## Synthetic or live classification

Live public-source retrieval plus pinned-source execution with synthetic dependencies. Not a live ABS integration test.

## Sanitization and redistribution notes

Only source identifiers, check names and outcomes retained. No developer credentials, host, ABS settings or catalog payloads read by this component check. The sanitizer was stubbed and no security conclusion about description sanitization is claimed.
