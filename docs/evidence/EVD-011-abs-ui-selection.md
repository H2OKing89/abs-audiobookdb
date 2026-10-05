# Rendered ABS edition selection

Status: Recorded  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID: EVD-011

SPIKE evidence; linked checks remain limited to the classification below.

## Source URL or fixture provenance

Two invented narrator recordings from SPIKE-003, rendered in disposable ABS; no metadata saved.

## Captured date and environment

2026-10-05 17:58 UTC; ABS 2.37.1, Playwright 1.63.0 and cached Chromium revision 1217.

## Version, commit or content hash

Digest-pinned ABS image in EVD-010; browser script is `spikes/SPIKE-001/ui_experiment.cjs`.

## Method and reproduction steps

Start `python3 spikes/SPIKE-001/live_experiment.py --keep-for-ui`; run `node spikes/SPIKE-001/ui_experiment.cjs /tmp/abs-spike-RUN/context.json` with the printed context path. Finish the waiting process for cleanup.

## Sanitized artifact path

[Successful UI result](SPIKE-001/ui-2026-10-05T175846141Z.json); [cards screenshot](SPIKE-001/ui-cards-2026-10-05T175846141Z.png); [selection A](SPIKE-001/ui-selection-A-2026-10-05T175846141Z.png); [selection B](SPIKE-001/ui-selection-B-2026-10-05T175846141Z.png). Earlier `ui-*.json` and incomplete screenshots are retained.

## Claims supported and limitations

Both narrator cards rendered; each selection pane contained its intended narrator and excluded the other. No item-write requests observed. Same-narrator language distinctions, full-cast selection and production usability remain unvalidated.

## Observed outcome

Pass after preserved selector/default-provider preparation failures. Match defaults to Google Books independently of the library provider. The successful script intercepts nonfixture searches. An earlier failed run may have issued a Google Books lookup containing only an invented title; older blanket no-upstream wording must not be read as verified absence of all external traffic.

## Synthetic or live classification

Actual browser UI against isolated ABS and invented fixtures, not the live library or AudiobookDB.

## Sanitization and redistribution notes

Screenshots contain invented books and local test account only. Login credentials remain in temporary mode-600 context; no traces, cookies or request headers archived.
