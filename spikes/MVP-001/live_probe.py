#!/usr/bin/env python3
"""Four delivered-adapter searches; at most 20 upstream cost units, no writes."""
import datetime
import argparse
import hashlib
import importlib.util
import json
import secrets
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = 'abs-audiobookdb:mvp-20261005'


def docker(*args):
    return subprocess.run(['docker', *args], capture_output=True, text=True, timeout=60, check=True).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remaining-after-schema-failure', action='store_true', help='Only cold/warm/invalid; prior failed auth+search spent four documented units')
    args = parser.parse_args()
    name = 'abs-mvp-live-' + secrets.token_hex(4)
    checks = []
    outcome, reason, cleanup = 'Incomplete', None, False
    spec = importlib.util.spec_from_file_location('dev', ROOT / 'spikes/contract-probes/probe.py')
    dev = importlib.util.module_from_spec(spec); spec.loader.exec_module(dev)
    config = dev.load_config()
    key, _ = dev.key_file(config, 'AUDIOBOOKDB_API_FILE', 'audiobookdb_api_key')
    contact = config.get('AUDIOBOOKDB_CONTACT', '')
    private = [key, contact, config.get('AUDIOBOOKSHELF_HOST', '')]
    created = False
    image_id = docker('image', 'inspect', IMAGE, '--format', '{{.Id}}')
    # Worst-case caps: title cold 12, title warm 1, exact ASIN 3, invalid key 1.
    # Stop immediately on unexpected failure; never retry a live search.
    try:
        assert contact
        with tempfile.TemporaryDirectory(prefix=name) as tmp:
            env = Path(tmp) / 'runtime.env'; env.write_text('AUDIOBOOKDB_CONTACT=' + contact + '\n'); env.chmod(0o600)
            docker('run', '-d', '--name', name, '--user', '99:100', '--read-only', '--memory', '256m',
                   '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                   '--env-file', str(env), '-p', '127.0.0.1::8080', IMAGE)
            created = True
        base = 'http://' + docker('port', name, '8080/tcp')
        docker('exec', name, '/adapter', 'health')
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        saved = None
        searches = [
            ('title_cold', {'query': 'the martian'}, key, 200, 12),
            ('title_warm', {'query': 'the martian'}, key, 200, 1),
            ('exact_asin', {'asin': 'B00B5HZGUG'}, key, 200, 3),
            ('invalid_key_warm_query', {'query': 'the martian'}, 'SYNTHETIC-INVALID-MVP', 401, 1),
        ]
        if args.remaining_after_schema_failure:
            searches = [s for s in searches if s[0] != 'exact_asin']
        for label, query, credential, expected, cap in searches:
            req = urllib.request.Request(base + '/search?' + urllib.parse.urlencode(query), headers={'Authorization': credential})
            started = time.monotonic()
            try:
                response = opener.open(req, timeout=9)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                raw = response.read(1048577); assert len(raw) <= 1048576
                result = json.loads(raw); status = response.code
            elapsed = time.monotonic() - started
            check = {'check': label, 'http_status': status, 'seconds': round(elapsed, 3), 'documented_cost_ceiling': cap, 'outcome': 'Pass' if status == expected and elapsed < 8 else 'Fail'}
            checks.append(check)
            assert check['outcome'] == 'Pass'
            if status == 200:
                matches = result['matches']; assert isinstance(matches, list) and 1 <= len(matches) <= 6
                check['match_count'] = len(matches)
                if label == 'title_cold':
                    saved = raw
                elif label == 'title_warm':
                    assert raw == saved
                else:
                    assert len(matches) == 1 and matches[0]['asin'] == 'B00B5HZGUG'
        logs = docker('logs', name); assert not any(v and v in logs for v in private)
        outcome = 'Pass'
    except Exception as error:
        reason = type(error).__name__
    finally:
        if created:
            result = subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=30); cleanup = result.returncode == 0
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        folder = ROOT / 'docs/evidence/MVP-001'; folder.mkdir(parents=True, exist_ok=True)
        record = {'captured_at_utc': stamp, 'classification': 'delivered_adapter_live_read_only_audiobookdb', 'outcome': outcome, 'stop_reason': reason, 'checks': checks, 'image_id': image_id, 'searches_attempted': len(checks), 'total_documented_cost_ceiling': sum(c['documented_cost_ceiling'] for c in checks), 'prior_failed_search_documented_cost': 4 if args.remaining_after_schema_failure else 0, 'temporary_container_removed': cleanup, 'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'limitations': 'No production key revoked; invalid key is synthetic. Counts/latencies only; mapped catalog content stays in memory. Prior four units inferred from auth+search and deterministic flattened-search decode failure in old source, not measured quota accounting. Per-request ceilings are not measured actual API accounting.'}
        target = folder / ('live-' + stamp + '.json'); encoded = json.dumps(record, indent=2); assert not any(v and v in encoded for v in private); target.write_text(encoded + '\n')
        print('Live delivered adapter: ' + outcome + '. Evidence: ' + str(target.relative_to(ROOT)))
    return 0 if outcome == 'Pass' and cleanup else 1


if __name__ == '__main__':
    raise SystemExit(main())
