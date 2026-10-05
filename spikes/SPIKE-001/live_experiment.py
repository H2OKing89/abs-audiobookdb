#!/usr/bin/env python3
"""Disposable ABS/provider integration, with synthetic local credentials only."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = 'ghcr.io/advplyr/audiobookshelf@sha256:581d68b2a6fc7ebf58d81c878a9f387cbbc0d88ac9d37b298b9cee10168af85b'


def docker(*args):
    result = subprocess.run(['docker', *args], check=True, text=True, capture_output=True, timeout=90)
    return result.stdout.strip()


def request(base, path, body=None, token=None, method=None, timeout=25):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(base + path, headers=headers,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 method=method)
    try:
        response = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        raw = response.read(1048577)
        assert len(raw) <= 1048576
        try:
            data = json.loads(raw)
        except ValueError:
            data = None
        return response.status, data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keep-for-ui', action='store_true', help='Wait for stdin after probes, keeping only disposable fixtures alive')
    args = parser.parse_args()
    label = 'abs-spike-' + secrets.token_hex(4)
    lab = Path(tempfile.mkdtemp(prefix=label + '-'))
    for name in ('config', 'metadata', 'audiobooks'):
        (lab / name).mkdir()
    fixture = label + '-provider'
    abs_name = label + '-abs'
    created = []
    checks = []
    outcome = 'Incomplete'
    reason = None
    private_values = []
    try:
        module_spec = importlib.util.spec_from_file_location('mapping_experiment', ROOT / 'spikes/SPIKE-003/experiment.py')
        mapping = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(mapping)
        fixtures = json.loads((ROOT / 'spikes/SPIKE-003/fixtures.json').read_text())
        inputs = next(c['input'] for c in fixtures['cases'] if c['name'] == 'multiple-recordings')
        match_data = mapping.map_case(inputs)['matches']
        for match in match_data:
            match.pop('cover', None)  # No external image fetch is needed in the isolated UI.
        (lab / 'matches.json').write_text(json.dumps(match_data))
        audio = lab / 'audiobooks' / 'Synthetic Author' / 'Invented Example'
        audio.mkdir(parents=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=22050:cl=mono', '-t', '1',
                        '-metadata', 'title=Invented Example', '-metadata', 'artist=Synthetic Author',
                        '-codec:a', 'libmp3lame', str(audio / 'sample.mp3')], check=True, timeout=20, capture_output=True)
        docker('network', 'create', '--label', 'abs.spike=' + label, label)
        created.append(('network', label))
        docker('run', '-d', '--name', fixture, '--label', 'abs.spike=' + label, '--network', label,
               '--network-alias', 'spike-provider', '--user', str(os.getuid()) + ':' + str(os.getgid()),
               '-p', '127.0.0.1::8000', '--mount', 'type=bind,src=' + str(lab) + ',dst=/lab,readonly',
               '--mount', 'type=bind,src=' + str(Path(__file__).with_name('fixture_server.py')) + ',dst=/fixture.py,readonly',
               'python:3.10-slim', 'python', '/fixture.py')
        created.append(('container', fixture))
        provider_base = 'http://' + docker('port', fixture, '8000/tcp')
        docker('run', '-d', '--name', abs_name, '--label', 'abs.spike=' + label, '--network', label,
               '--user', str(os.getuid()) + ':' + str(os.getgid()), '-p', '127.0.0.1::80',
               '--mount', 'type=bind,src=' + str(lab / 'config') + ',dst=/config',
               '--mount', 'type=bind,src=' + str(lab / 'metadata') + ',dst=/metadata',
               '--mount', 'type=bind,src=' + str(lab / 'audiobooks') + ',dst=/audiobooks,readonly',
               IMAGE)
        created.append(('container', abs_name))
        base = 'http://' + docker('port', abs_name, '80/tcp')
        for _ in range(40):
            try:
                status, data = request(base, '/status', timeout=2)
                if status == 200:
                    break
            except (OSError, TimeoutError):
                pass
            time.sleep(0.5)
        else:
            raise RuntimeError('isolated_abs_startup_failed')
        assert data.get('serverVersion') == '2.37.1'
        password = secrets.token_urlsafe(24)
        private_values.extend([password, 'SYNTHETIC-SPIKE-AUTH'])
        assert request(base, '/init', {'newRoot': {'username': 'spike-admin', 'password': password}})[0] == 200
        status, login = request(base, '/login', {'username': 'spike-admin', 'password': password})
        assert status == 200
        token = login['user']['accessToken']
        private_values.append(token)
        status, provider = request(base, '/api/custom-metadata-providers',
            {'name': 'Synthetic Spike Provider', 'url': 'http://spike-provider:8000', 'mediaType': 'book',
             'authHeaderValue': 'SYNTHETIC-SPIKE-AUTH'}, token)
        assert status == 200
        slug = 'custom-' + provider['provider']['id']
        status, library = request(base, '/api/libraries', {'name': 'Synthetic Spike Library', 'mediaType': 'book',
                               'folders': [{'fullPath': '/audiobooks'}], 'provider': slug}, token)
        assert status == 200
        library_id = library['id']
        assert request(base, '/api/libraries/' + library_id + '/scan', {}, token)[0] == 200
        for _ in range(40):
            _, listing = request(base, '/api/libraries/' + library_id + '/items', token=token)
            if listing.get('results'):
                item_id = listing['results'][0]['id']
                break
            time.sleep(0.5)
        else:
            raise RuntimeError('synthetic_audio_scan_failed')
        query = '/api/search/books?' + urllib.parse.urlencode({'provider': slug, 'title': 'Invented Example',
                                                                'author': 'Synthetic Author', 'isbn': '9780000000002'})
        def search():
            return request(base, query, token=token)
        status, result = search()
        assert status == 200 and len(result) == 2
        assert [m['narrator'] for m in result] == ['Narrator A', 'Narrator B']
        _, capture = request(provider_base, '/captures')
        assert capture[-1]['auth_matches_expected']
        assert capture[-1]['query_keys'] == ['author', 'mediaType', 'query']
        checks.append({'check': 'actual_request_raw_auth_params_and_two_editions', 'outcome': 'Pass',
                       'capture': capture[-1], 'note': 'ISBN supplied to search API was not forwarded by its controller.'})
        for seconds in (1, 5, 11):
            request(provider_base, '/control', {'delay': seconds})
            start = time.monotonic()
            status, result = search()
            elapsed = time.monotonic() - start
            if seconds < 10:
                assert status == 200 and len(result) == 2 and elapsed >= seconds
            else:
                assert status == 200 and result == [] and 9 <= elapsed <= 12
            checks.append({'check': 'delay_' + str(seconds), 'outcome': 'Pass', 'elapsed_seconds': round(elapsed, 3),
                           'match_count': len(result), 'http_status': status})
        request(provider_base, '/control', {'delay': 0})
        for fixture_status in (400, 401, 404, 429, 500, 503):
            request(provider_base, '/control', {'status': fixture_status})
            status, result = search()
            assert status == 200 and result == []
            checks.append({'check': 'provider_http_' + str(fixture_status), 'outcome': 'Pass',
                           'abs_http_status': status, 'match_count': 0})
        request(provider_base, '/control', {'status': 200, 'malformed': True})
        status, result = search()
        assert status == 200 and result == []
        checks.append({'check': 'malformed_success_envelope', 'outcome': 'Pass', 'abs_http_status': status, 'match_count': 0})
        request(provider_base, '/control', {'malformed': False})
        rotated_auth = 'SYNTHETIC-SPIKE-ROTATED'
        private_values.append(rotated_auth)
        request(provider_base, '/control', {'expected_auth': rotated_auth})
        status, rotated = request(base, '/api/custom-metadata-providers',
            {'name': 'Synthetic Rotated Provider', 'url': 'http://spike-provider:8000', 'mediaType': 'book',
             'authHeaderValue': rotated_auth}, token)
        assert status == 200
        rotated_slug = 'custom-' + rotated['provider']['id']
        rotated_query = '/api/search/books?' + urllib.parse.urlencode({'provider': rotated_slug, 'title': 'Invented Example'})
        status, result = request(base, rotated_query, token=token)
        assert status == 200 and len(result) == 2
        _, captures = request(provider_base, '/captures')
        assert captures[-1]['auth_matches_expected']
        status, result = search()
        assert status == 200 and result == []
        checks.append({'check': 'replacement_key_forwarded_old_key_rejected', 'outcome': 'Pass',
                       'note': 'Rotation modeled by a replacement ABS provider; no upstream key revocation claim.'})
        request(provider_base, '/control', {'expected_auth': 'SYNTHETIC-SPIKE-AUTH'})
        logs = docker('logs', abs_name)
        assert not any(value in logs for value in private_values)
        checks.append({'check': 'isolated_abs_logs_secret_scan', 'outcome': 'Pass'})
        context = {'base': base, 'provider_base': provider_base, 'username': 'spike-admin', 'password': password,
                   'library_id': library_id, 'item_id': item_id, 'provider_slug': slug, 'lab': str(lab)}
        context_path = lab / 'context.json'
        context_path.write_text(json.dumps(context))
        context_path.chmod(0o600)
        print('Isolated ABS API capture, timeout and error checks passed.', flush=True)
        if args.keep_for_ui:
            print('UI context: ' + str(context_path), flush=True)
            print('Waiting for UI completion; send a line to clean up only these spike fixtures.', flush=True)
            sys.stdin.readline()
        outcome = 'Pass'
    except Exception as error:
        reason = type(error).__name__  # Never output response/token/exception text.
        print('Isolated experiment incomplete: ' + reason, flush=True)
    finally:
        cleanup = []
        for kind, name in reversed(created):
            try:
                docker('rm', '-f', name) if kind == 'container' else docker('network', 'rm', name)
                cleanup.append({'resource_type': kind, 'removed': True})
            except Exception:
                cleanup.append({'resource_type': kind, 'removed': False})
        folder = ROOT / 'docs/evidence/SPIKE-001'
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        result = {'captured_at_utc': stamp, 'classification': 'isolated_abs_live_integration_with_synthetic_provider',
                  'image': IMAGE, 'outcome': outcome, 'stop_reason': reason, 'checks': checks, 'cleanup': cleanup,
                  'limitations': 'Temporary ABS only; no production credentials/settings accessed. UI result is a separate record. This is not an upstream AudiobookDB timeout or final Unraid deployment test.'}
        output = folder / ('integration-' + stamp + '.json')
        encoded = json.dumps(result, indent=2)
        assert not any(v in encoded for v in private_values)
        with output.open('x') as f:
            f.write(encoded + '\n')
        shutil.rmtree(lab, ignore_errors=True)
        print('Evidence: ' + str(output.relative_to(ROOT)), flush=True)
    return 0 if outcome == 'Pass' and all(r['removed'] for r in cleanup) else 1


if __name__ == '__main__':
    raise SystemExit(main())
