# Repository Guidelines

## Project Structure & Module Organization

This repository implements a read-only Go metadata adapter between Audiobookshelf (ABS) and AudiobookDB, with planning documents and executable experiments.

- `README.md`: workflow and document index.
- `docs/planning/`: numbered scope, contracts, architecture, verification, risks, MVP, sources, and phase-gate documents.
- `docs/templates/`: templates for planning, decisions, spikes, evidence, and reviews.
- `docs/decisions/`, `docs/spikes/`, `docs/evidence/`: decision records, experiment records, and sanitized supporting evidence.
- `docs/CHANGELOG.md`: changes and affected checks.
- `spikes/`: experimental code after Gate A; each experiment must link its plan, reproduction instructions, and results.

Production code and tests live in `cmd/abs-audiobookdb/` and `internal/` following the private Gate C review. Executable experiments and their reproduction workflows remain in `spikes/`.

## Build, Test, and Development Commands

Run production checks with `go test -race ./...` and `go vet ./...`; build with `go build -trimpath -o bin/abs-audiobookdb ./cmd/abs-audiobookdb`. Each executable experiment documents its test workflow in its `spikes/` README and linked spike record. Useful documentation commands include:

- `rg --files docs spikes`: list planning and experiment files.
- `cp docs/templates/spike.md docs/spikes/SPIKE-NNN-description.md`: create a spike record; choose the next unused ID and replace all placeholders.
- `rg -n 'TBD|Not run|Pending' docs`: locate unresolved planning items; results do not establish gate completion.

Document exact reproduction commands in each spike record.

## Coding Style & Naming Conventions

Use Markdown headings, concise explanations, relative links, and the existing numbered, kebab-case planning filenames. Preserve template section order and metadata fields: Status, Updated, Owner, and Baseline. Allocate stable IDs (`REQ`, `VER`, `VAL`, `Q`, `RISK`, `ADR`, `SPIKE`, `SRC`, `EVD`, `CHANGE`); never reuse them. Format future Go code with `gofmt` and its standard tab indentation.

## Testing Guidelines

Follow `docs/planning/04-verification-validation.md`. No testing framework or coverage threshold is configured. Record actual outcomes, versions, dates, fixture provenance, and evidence links for each check. Preserve failures; blocked or unrun checks never count as passes. Rerun affected checks after changes.

## Commit & Pull Request Guidelines

Git history is unavailable in this checkout, so commit conventions cannot be verified. Use concise, imperative messages describing the changed document or behavior. PRs should explain the change, link affected record IDs, report verification outcomes, and update the changelog when planning changes.

## Security & Phase Gates

Keep credentials in ignored `.env` or `secrets/`. Never commit authenticated headers, credentials, or unsanitized dumps. Treat API claims as hypotheses until supported by evidence. Follow `docs/planning/08-phase-gates.md`; production implementation starts only after Gate C.
