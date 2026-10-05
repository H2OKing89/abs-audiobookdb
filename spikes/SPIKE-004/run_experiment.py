#!/usr/bin/env python3
"""Capture bounded race-test evidence; never reads development credentials."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
run = subprocess.run(['go', 'test', '-race', '-v', './...'], cwd=HERE,
                     capture_output=True, text=True, timeout=120)
raw = run.stdout + run.stderr
assert len(raw) <= 1048576
sentinels = ['SYNTHETIC-SECRET-A', 'SYNTHETIC-SECRET-B']
leaked = any(s in raw for s in sentinels)
for secret in sentinels:
    raw = raw.replace(secret, '[redacted synthetic key]')
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
folder = ROOT / 'docs/evidence/SPIKE-004'
folder.mkdir(parents=True, exist_ok=True)
transcript = folder / ('race-' + stamp + '.txt')
transcript.write_text(raw)
record = {'captured_at_utc': stamp, 'classification': 'synthetic_go_httptest_race_experiment',
          'outcome': 'Pass' if run.returncode == 0 and not leaked else 'Fail', 'exit_code': run.returncode,
          'go_version': subprocess.run(['go', 'version'], capture_output=True, text=True, check=True).stdout.strip(),
          'command': 'go test -race -v ./...', 'transcript': transcript.name, 'sentinel_output_scan_pass': not leaked,
          'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                            [HERE / 'lab.go', HERE / 'lab_test.go', HERE / 'go.mod']},
          'limitations': 'Synthetic validation endpoint, keys, data and timings only; no live revocation, full memory bound or real end-to-end latency established.'}
output = folder / ('bounds-' + stamp + '.json')
output.write_text(json.dumps(record, indent=2) + '\n')
print('Bounds outcome: ' + record['outcome'] + '. Evidence: ' + str(output.relative_to(ROOT)))
raise SystemExit(0 if record['outcome'] == 'Pass' else 1)
