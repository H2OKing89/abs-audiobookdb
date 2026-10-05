# Edition-mapping fixtures

Plan: [SPIKE-003](../../docs/spikes/SPIKE-003-edition-mapping.md). Inputs are in [fixtures.json](fixtures.json). All values are invented locally; they are not copied API payloads or catalog records.

The eleven scenarios cover every category in the verification matrix plus duplicate release IDs. Each carries expected properties and linked check IDs. Fixture metadata describes its initial preparation; current execution outcomes are in the spike/evidence records. The ISBN scenario is conditional because upstream exact lookup remains unresolved. The ambiguous-title case includes `alternateBook` and `alternateReleases` as a second work; the experiment associates each release with its book. Those fixture fields are not upstream wire format.

Inspect the inputs with:

```sh
python3 -m json.tool spikes/SPIKE-003/fixtures.json
```

These invented inputs are exercised by the mapper and the two-narrator browser case. Exact ISBN support remains conditional; use string series sequences to preserve zero under the observed ABS normalizer.

The isolated experiment is now available:

```sh
python3 spikes/SPIKE-003/experiment.py
```

It checks eleven scenarios on three deterministic runs each, supported ABS field types, release deduplication and fallback/rounding/unknown-identifier boundaries. Provisional rules are listed in the spike plan. It uses no network or credentials and saves only synthetic outcome summaries. Passing ISBN fixture selection is conditional evidence, not proof of upstream lookup support; live ABS UI validation remains separate.
