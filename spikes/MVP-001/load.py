#!/usr/bin/env python3
"""SPIKE-007: bounded synthetic load; never contacts a live API or ABS."""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
import secrets
import shutil
import ssl
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def command(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.PIPE, timeout=90).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', default='abs-audiobookdb:local-ci')
    parser.add_argument('--output', type=Path, help='Write evidence here instead of the repository evidence directory')
    parser.add_argument('--warm-seconds', type=int, default=60, choices=range(15, 181), metavar='15..180')
    args = parser.parse_args()
    identity = 'abs-load-' + secrets.token_hex(4)
    network, adapter, upstream = identity, identity + '-adapter', identity + '-upstream'
    lab = Path(tempfile.mkdtemp(prefix=identity))
    lab.chmod(0o755)
    created = []
    samples, results, cleanup = [], [], []
    stop = threading.Event()
    sampler = None
    outcome, stage, reason = 'Incomplete', 'prepare', None
    started = time.monotonic()
    metadata = {}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def request(base, path, expected=200, tls=False):
        headers = {} if tls else {'Authorization': 'SYNTHETIC-LOAD-KEY'}
        req = urllib.request.Request(base + path, headers=headers)
        client = trusted if tls else opener
        try:
            response = client.open(req, timeout=10)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = response.read(1048577)
            assert response.status == expected, f'Expected {expected}, received {response.status}'
            assert len(raw) <= 1048576, 'Mapped response exceeded cap'
            return json.loads(raw)

    def search(query, expected=200):
        start = time.monotonic()
        body = request(adapter_base, '/search?' + urllib.parse.urlencode({'query': query}), expected)
        elapsed = time.monotonic() - start
        assert elapsed < 8.5, 'Response missed the adapter deadline plus measurement tolerance'
        if expected == 200:
            assert len(body['matches']) == 6, 'Incomplete selected recording results'
        return elapsed

    def observe_memory(pid):
        while not stop.is_set():
            values = {}
            try:
                for line in Path(f'/proc/{pid}/status').read_text().splitlines():
                    name, _, value = line.partition(':')
                    if name in ('VmRSS', 'VmHWM'):
                        values[name] = int(value.split()[0]) * 1024
                samples.append(values)
            except (OSError, ValueError):
                pass
            stop.wait(0.1)

    try:
        metadata['image_id'] = command('docker', 'image', 'inspect', args.image, '--format', '{{.Id}}')
        metadata['build'] = json.loads(command('docker', 'run', '--rm', '--network', 'none', args.image, 'version'))
        command('openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
                '-subj', '/CN=load-fixture.invalid', '-addext', 'subjectAltName=DNS:upstream,IP:127.0.0.1',
                '-keyout', str(lab / 'key.pem'), '-out', str(lab / 'cert.pem'))
        (lab / 'key.pem').chmod(0o600)
        shutil.copyfile(HERE / 'load_upstream.py', lab / 'fixture.py')
        context = ssl.create_default_context(cafile=str(lab / 'cert.pem'))
        trusted = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=context))
        # Published loopback ports are disabled on internal networks by this
        # Docker version. Use a disposable bridge with only synthetic endpoints.
        command('docker', 'network', 'create', network)
        created.append(('network', network))
        created.append(('container', upstream))
        command('docker', 'run', '-d', '--name', upstream, '--network', network, '--network-alias', 'upstream',
                '--read-only', '-p', '127.0.0.1::8443', '--mount', f'type=bind,src={lab},dst=/lab,readonly',
                'python:3.10-slim', 'python', '-B', '/lab/fixture.py')
        upstream_base = 'https://' + command('docker', 'port', upstream, '8443/tcp')
        created.append(('container', adapter))
        command('docker', 'run', '-d', '--name', adapter, '--network', network, '--network-alias', 'adapter',
                '--user', '99:100', '--read-only', '--memory', '256m', '--memory-swap', '256m',
                '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '-p', '127.0.0.1::8080',
                '--mount', f'type=bind,src={lab},dst=/lab,readonly',
                '-e', 'AUDIOBOOKDB_CONTACT=operator@example.invalid', '-e', 'GOMEMLIMIT=192MiB',
                '-e', 'AUDIOBOOKDB_BASE_URL=https://upstream:8443/api', '-e', 'SSL_CERT_FILE=/lab/cert.pem', args.image)
        adapter_base = 'http://' + command('docker', 'port', adapter, '8080/tcp')
        stage = 'startup'
        for attempt in range(60):
            try:
                request(adapter_base, '/health')
                request(upstream_base, '/stats', tls=True)
                break
            except (OSError, AssertionError):
                time.sleep(0.2)
        else:
            raise RuntimeError('Fixture startup timeout')
        pid = int(command('docker', 'inspect', adapter, '--format', '{{.State.Pid}}'))
        sampler = threading.Thread(target=observe_memory, args=(pid,), daemon=True)
        sampler.start()

        stage = 'large-cold-cache-turnover'
        cold = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            for batch in range(8):
                jobs = [pool.submit(search, f'Synthetic memory fixture {batch * 3 + n}') for n in range(3)]
                cold.extend(job.result() for job in jobs)
        results.append({'check': '24_large_cold_searches_at_three_concurrent', 'outcome': 'Pass',
                        'max_seconds': round(max(cold), 3), 'matches_each': 6, 'detail_response_bytes': 900 * 1024})

        stage = 'cache-eviction'
        before = request(upstream_base, '/stats', tls=True)['calls']
        search('Synthetic memory fixture 0')
        after = request(upstream_base, '/stats', tls=True)['calls']
        assert after - before == 10, 'Old large response was not evicted'
        results.append({'check': 'large_entry_cache_turnover', 'outcome': 'Pass', 'refetch_calls': after - before})

        stage = 'sustained-warm-searches'
        before = request(upstream_base, '/stats', tls=True)['calls']
        search('Synthetic memory fixture 23')
        after = request(upstream_base, '/stats', tls=True)['calls']
        assert after - before == 1, 'Warm cache bypassed fresh auth or repeated detail reads'
        deadline = time.monotonic() + args.warm_seconds

        def warm_worker(n):
            count, maximum = 0, 0.0
            while time.monotonic() < deadline:
                maximum = max(maximum, search(f'Synthetic memory fixture {21 + n}'))
                count += 1
            return count, maximum

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            warm = list(pool.map(warm_worker, range(3)))
        results.append({'check': 'sustained_three_worker_warm_searches', 'outcome': 'Pass',
                        'seconds': args.warm_seconds, 'searches': sum(n for n, _ in warm),
                        'max_seconds': round(max(t for _, t in warm), 3), 'initial_warm_auth_calls': 1})

        stage = 'slow-and-oversized-upstream'
        for query, status, code in [('Synthetic slow response', 504, 'deadline'),
                                    ('Synthetic oversized response', 502, 'upstream_size'),
                                    ('Synthetic oversized mapping', 502, 'upstream_size')]:
            body = request(adapter_base, '/search?' + urllib.parse.urlencode({'query': query}), status)
            assert body['error'] == code
            results.append({'check': code + '_' + query.removeprefix('Synthetic ').replace(' ', '_'),
                            'outcome': 'Pass', 'status': status})
        request(adapter_base, '/health')
        state = json.loads(command('docker', 'inspect', adapter))[0]['State']
        assert state['Running'] and not state['OOMKilled']
        assert int(command('docker', 'inspect', adapter, '--format', '{{.RestartCount}}')) == 0
        assert samples and all('VmHWM' in s for s in samples), 'Host RSS sampling unavailable'
        peak = max(s['VmHWM'] for s in samples)
        assert peak < 256 * 1024 * 1024, 'Observed process RSS reached the memory limit'
        metadata['memory'] = {'samples': len(samples), 'peak_process_rss_bytes': peak,
                              'last_process_rss_bytes': samples[-1]['VmRSS'], 'limit_bytes': 256 * 1024 * 1024,
                              'oom_killed': False, 'restarts': 0}
        logs = command('docker', 'logs', adapter)
        assert 'SYNTHETIC-LOAD-KEY' not in logs, 'Sentinel credential leaked in logs'
        stage = 'complete'
        outcome = 'Pass'
    except Exception as error:
        reason = type(error).__name__ + ': ' + str(error)
    finally:
        stop.set()
        if sampler:
            sampler.join(timeout=2)
        for kind, resource in reversed(created):
            result = subprocess.run(['docker', 'rm', '-f', resource] if kind == 'container'
                                    else ['docker', 'network', 'rm', resource], capture_output=True, timeout=30)
            cleanup.append({'resource': kind, 'removed': result.returncode == 0})
        shutil.rmtree(lab)
        if not all(item['removed'] for item in cleanup):
            outcome = 'Incomplete'
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        artifact = args.output or ROOT / 'docs/evidence/MVP-001' / ('load-' + stamp + '.json')
        artifact.parent.mkdir(parents=True, exist_ok=True)
        record = {'captured_at_utc': stamp, 'classification': 'synthetic_isolated_container_load',
                  'outcome': outcome, 'stage': stage, 'reason': reason,
                  'duration_seconds': round(time.monotonic() - started, 3), **metadata,
                  'checks': results, 'cleanup': cleanup,
                  'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'limitations': 'Local synthetic workload only; process RSS is not total cgroup memory. No live API, ABS or Unraid workload; no latency or production memory guarantee.'}
        artifact.write_text(json.dumps(record, indent=2) + '\n')
        print('Synthetic load: ' + outcome + '; evidence: ' + str(artifact))
    return 0 if outcome == 'Pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
