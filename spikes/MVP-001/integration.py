#!/usr/bin/env python3
"""Run delivered adapter with synthetic TLS upstream and isolated ABS/UI."""
import copy
import datetime
import hashlib
import importlib.util
import json
import os
import secrets
import shutil
import ssl
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ADAPTER = 'abs-audiobookdb:mvp-20261005'
ABS = 'ghcr.io/advplyr/audiobookshelf@sha256:581d68b2a6fc7ebf58d81c878a9f387cbbc0d88ac9d37b298b9cee10168af85b'


def run(args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, check=True, timeout=90, **kwargs).stdout.strip()


def request(base, path, body=None, token=None, raw_key=None, context=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if raw_key:
        headers['Authorization'] = raw_key
    req = urllib.request.Request(base + path, headers=headers,
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        response = urllib.request.urlopen(req, context=context, timeout=10)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        raw = response.read(1048577)
        assert len(raw) <= 1048576
        try:
            body = json.loads(raw)
        except ValueError:
            body = None  # ABS scan acknowledgements may have an empty body.
        return response.status, body


def main():
    label = 'abs-mvp-' + secrets.token_hex(4)
    lab = Path(tempfile.mkdtemp(prefix=label + '-'))
    lab.chmod(0o755)
    created, checks, cleanup = [], [], []
    stage, outcome, reason = 'prepare', 'Incomplete', None
    private = ['SYNTHETIC-MVP-KEY', 'SYNTHETIC-INVALID-KEY']
    image_id = run(['docker', 'image', 'inspect', ADAPTER, '--format', '{{.Id}}'])
    try:
        fixtures = json.loads((ROOT / 'spikes/SPIKE-003/fixtures.json').read_text())
        data = copy.deepcopy(next(c['input'] for c in fixtures['cases'] if c['name'] == 'multiple-recordings'))
        for release in data['releases']:
            release['images'] = []
        data['book']['coverImage'] = None
        cast = copy.deepcopy(data['releases'][0]); cast['id'] = 'synthetic-cast'
        cast['people'] = [{'role': {'name': 'Narrator'}, 'person': {'name': 'Full Cast'}}]
        french = copy.deepcopy(data['releases'][0]); french['id'] = 'synthetic-french'
        french['subtitle'] = 'French edition'; french['language'] = {'name': 'French'}
        data['releases'] += [cast, french]
        data['book']['releases'] = [{'id': r['id']} for r in data['releases']]
        (lab / 'data.json').write_text(json.dumps(data))
        run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
             '-subj', '/CN=synthetic-mvp.invalid', '-addext',
             'subjectAltName=DNS:upstream,DNS:adapter,IP:127.0.0.1',
             '-keyout', str(lab / 'key.pem'), '-out', str(lab / 'cert.pem')])
        os.chown(lab / 'key.pem', -1, 100); (lab / 'key.pem').chmod(0o640)
        trust = ssl.create_default_context(cafile=str(lab / 'cert.pem'))
        for directory in ('config', 'metadata', 'audiobooks'):
            (lab / directory).mkdir()
        audio = lab / 'audiobooks/Synthetic Author/Invented Example'; audio.mkdir(parents=True)
        run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=22050:cl=mono', '-t', '1',
             '-metadata', 'title=Invented Example', '-metadata', 'artist=Synthetic Author',
             '-codec:a', 'libmp3lame', str(audio / 'sample.mp3')])
        run(['docker', 'network', 'create', label]); created.append(('network', label))
        names = {n: label + '-' + n for n in ('upstream', 'adapter', 'abs')}
        for name in names.values():
            created.append(('container', name))
        run(['docker', 'run', '-d', '--name', names['upstream'], '--network', label,
             '--network-alias', 'upstream', '-p', '127.0.0.1::8443',
             '--user', '99:100', '--read-only', '--mount', 'type=bind,src=' + str(lab) + ',dst=/lab,readonly',
             '--mount', 'type=bind,src=' + str(HERE / 'upstream_fixture.py') + ',dst=/fixture.py,readonly',
             'python:3.10-slim', 'python', '/fixture.py'])
        common = ['--network', label, '--network-alias', 'adapter', '--user', '99:100', '--read-only',
                  '--memory', '256m', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                  '--mount', 'type=bind,src=' + str(lab) + ',dst=/lab,readonly',
                  '-e', 'AUDIOBOOKDB_CONTACT=operator@example.invalid',
                  '-e', 'AUDIOBOOKDB_BASE_URL=https://upstream:8443/api', '-e', 'SSL_CERT_FILE=/lab/cert.pem']
        run(['docker', 'run', '-d', '--name', names['adapter'], *common, '-p', '127.0.0.1::8080', ADAPTER])
        run(['docker', 'run', '-d', '--name', names['abs'], '--network', label,
             '--user', str(os.getuid()) + ':' + str(os.getgid()), '-p', '127.0.0.1::80',
             '--mount', 'type=bind,src=' + str(lab / 'config') + ',dst=/config',
             '--mount', 'type=bind,src=' + str(lab / 'metadata') + ',dst=/metadata',
             '--mount', 'type=bind,src=' + str(lab / 'audiobooks') + ',dst=/audiobooks,readonly', ABS])
        adapter_base = 'http://' + run(['docker', 'port', names['adapter'], '8080/tcp'])
        upstream_base = 'https://' + run(['docker', 'port', names['upstream'], '8443/tcp'])
        abs_base = 'http://' + run(['docker', 'port', names['abs'], '80/tcp'])
        stage = 'startup'
        for base, path in [(adapter_base, '/health'), (abs_base, '/status')]:
            for _ in range(40):
                try:
                    status, _ = request(base, path)
                    if status == 200:
                        break
                except (OSError, TimeoutError):
                    pass
                time.sleep(0.25)
            else:
                raise RuntimeError('startup')
        run(['docker', 'exec', names['adapter'], '/adapter', 'health'])
        stage = 'cold-warm-rejection'
        query = '/search?query=Invented+Example&author=Synthetic+Author'
        start = time.monotonic(); status, cold = request(adapter_base, query, raw_key=private[0]); elapsed = time.monotonic() - start
        assert status == 200 and len(cold['matches']) == 4 and elapsed < 8
        assert [m['narrator'] for m in cold['matches']] == ['Narrator A', 'Narrator B', 'Full Cast', 'Narrator A']
        assert cold['matches'][3]['language'] == 'French'
        before = request(upstream_base, '/stats', context=trust)[1]['calls']
        start = time.monotonic(); status, warm = request(adapter_base, query, raw_key=private[0]); warm_elapsed = time.monotonic() - start
        assert status == 200 and warm == cold
        after = request(upstream_base, '/stats', context=trust)[1]['calls']; assert after == before + 1
        checks.append({'check': 'four_editions_cold_and_fresh_auth_warm', 'outcome': 'Pass', 'cold_seconds': round(elapsed, 3), 'warm_seconds': round(warm_elapsed, 3), 'cold_upstream_attempts': before, 'warm_upstream_attempts': 1})
        assert request(adapter_base, query, raw_key=private[1])[0] == 401
        request(upstream_base, '/control', {'reject': True}, context=trust)
        assert request(adapter_base, query, raw_key=private[0])[0] == 401
        request(upstream_base, '/control', {'reject': False}, context=trust)
        checks.append({'check': 'invalid_key_and_fixture_revocation_reject_warm_cache', 'outcome': 'Pass'})
        stage = 'abs'
        password = secrets.token_urlsafe(24); private.append(password)
        assert request(abs_base, '/init', {'newRoot': {'username': 'mvp-admin', 'password': password}})[0] == 200
        status, login = request(abs_base, '/login', {'username': 'mvp-admin', 'password': password}); assert status == 200
        token = login['user']['accessToken']; private.append(token)
        status, result = request(abs_base, '/api/custom-metadata-providers',
            {'name': 'Synthetic MVP Provider', 'url': 'http://adapter:8080', 'mediaType': 'book', 'authHeaderValue': private[0]}, token=token); assert status == 200
        slug = 'custom-' + result['provider']['id']
        status, library = request(abs_base, '/api/libraries', {'name': 'Synthetic MVP Library', 'mediaType': 'book', 'folders': [{'fullPath': '/audiobooks'}], 'provider': slug}, token=token); assert status == 200
        library_id = library['id']; assert request(abs_base, '/api/libraries/' + library_id + '/scan', {}, token=token)[0] == 200
        for _ in range(40):
            listing = request(abs_base, '/api/libraries/' + library_id + '/items', token=token)[1]
            if listing.get('results'):
                item_id = listing['results'][0]['id']; break
            time.sleep(0.25)
        else:
            raise RuntimeError('scan')
        path = '/api/search/books?' + urllib.parse.urlencode({'provider': slug, 'title': 'Invented Example', 'author': 'Synthetic Author'})
        status, matches = request(abs_base, path, token=token); assert status == 200 and len(matches) == 4
        checks.append({'check': 'abs_2_37_1_delivered_adapter_four_matches', 'outcome': 'Pass'})
        context_path = lab / 'context.json'
        context_path.write_text(json.dumps({'base': abs_base, 'username': 'mvp-admin', 'password': password, 'item_id': item_id, 'provider_slug': slug}))
        context_path.chmod(0o600)
        stage = 'ui'; ui = json.loads(run(['node', str(HERE / 'ui.cjs'), str(context_path)])); assert ui['outcome'] == 'Pass'; checks.extend(ui['checks'])
        for name in (names['adapter'], names['abs']):
            logs = run(['docker', 'logs', name]); assert not any(v in logs for v in private)
        checks.append({'check': 'adapter_and_abs_private_log_scan', 'outcome': 'Pass'})
        state = json.loads(run(['docker', 'inspect', names['adapter'], '--format', '{{json .HostConfig.Memory}}']))
        assert state == 256 << 20
        identity = run(['docker', 'inspect', names['adapter'], '--format', '{{.Config.User}}'])
        assert identity == '99:100'
        checks.append({'check': 'container_256_mib_limit_and_uid_gid', 'outcome': 'Pass', 'user': identity})
        stage = 'stop'; started = time.monotonic(); run(['docker', 'stop', '-t', '10', names['adapter']]); stop_elapsed = time.monotonic() - started
        assert stop_elapsed < 10 and run(['docker', 'inspect', names['adapter'], '--format', '{{.State.ExitCode}}']) == '0'
        checks.append({'check': 'delivered_graceful_shutdown', 'outcome': 'Pass', 'seconds': round(stop_elapsed, 3)})
        outcome = 'Pass'
    except Exception as error:
        reason = type(error).__name__
    finally:
        for kind, name in reversed(created):
            result = subprocess.run(['docker', 'rm', '-f', name] if kind == 'container' else ['docker', 'network', 'rm', name], capture_output=True, timeout=30)
            cleanup.append({'resource': kind, 'removed': result.returncode == 0})
        shutil.rmtree(lab)
        folder = ROOT / 'docs/evidence/MVP-001'; folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        record = {'captured_at_utc': stamp, 'classification': 'delivered_adapter_isolated_abs_and_synthetic_tls_upstream', 'outcome': outcome, 'stage': stage, 'stop_reason': reason, 'checks': checks, 'cleanup': cleanup, 'image': ADAPTER, 'image_id': image_id, 'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'limitations': 'Synthetic catalog/authentication only; separate real API and target deployment evidence. No live ABS library modified. Screenshots omitted; UI uses invented fixtures only. ABS match cards omit language/subtitle; selecting the duplicate narrator recording exposes language in its form.'}
        target = folder / ('integration-' + stamp + '.json'); encoded = json.dumps(record, indent=2)
        assert not any(v in encoded for v in private); target.write_text(encoded + '\n')
        print('Isolated integration: ' + outcome + ' at ' + stage + '. Evidence: ' + str(target.relative_to(ROOT)))
    return 0 if outcome == 'Pass' and all(c['removed'] for c in cleanup) else 1


if __name__ == '__main__':
    raise SystemExit(main())
