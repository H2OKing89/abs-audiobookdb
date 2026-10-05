#!/usr/bin/env python3
"""Bounded read-only auth/cost experiment. Never archives account/catalog data."""
import datetime
import hashlib
import importlib.util
import json
import platform
import re
import signal
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'https://audiobookdb.org/api'
AGENT = 'abs-audiobookdb-spikes/0.1 (personal development by Quentin)'


class Stop(Exception):
    pass


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    initial = load_module('contract_probe', 'spikes/contract-probes/probe.py')
    mapper = load_module('fixture_mapper', 'spikes/SPIKE-003/experiment.py')
    config = initial.load_config()
    key, _ = initial.key_file(config, 'AUDIOBOOKDB_API_FILE', 'audiobookdb_api_key')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), initial.NoRedirect(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    calls, cost, last = 0, 0, 0
    records, checks = [], []
    outcome, reason = 'Incomplete', None
    path_start, path_calls, path_cost = None, 0, 0

    def read(label, route, credential=key, body=None, expected=200, charge=1, auth=False):
        nonlocal calls, cost, last, path_calls, path_cost
        if calls >= 16 or cost + charge > 20:
            raise Stop('overall_budget')
        if path_start is not None and (path_calls >= 10 or path_cost + charge > 12):
            raise Stop('cold_path_budget')
        pause = max(0, 0.25 - (time.monotonic() - last))
        if pause:
            time.sleep(pause)
        remaining = 8 - (time.monotonic() - path_start) if path_start is not None else 2
        if remaining <= 0:
            raise Stop('cold_path_deadline')
        method = 'POST' if body is not None else 'GET'
        if method == 'POST' and route != '/search':
            raise Stop('mutation_rejected')
        headers = {'User-Agent': AGENT, 'Accept': 'application/json'}
        if credential is not None:
            headers['X-API-Key'] = credential
        if body is not None:
            headers['Content-Type'] = 'application/json'
        calls += 1
        cost += charge
        if path_start is not None:
            path_calls += 1
            path_cost += charge
        last = start = time.monotonic()
        record = {'check': label, 'method': method, 'documented_cost_cap': charge}
        records.append(record)
        previous = signal.signal(signal.SIGALRM, initial.deadline_expired)
        signal.setitimer(signal.ITIMER_REAL, min(2, remaining))
        try:
            request = urllib.request.Request(BASE + route, headers=headers,
                data=json.dumps(body).encode() if body is not None else None, method=method)
            try:
                response = opener.open(request, timeout=min(2, remaining))
            except urllib.error.HTTPError as error:
                response = error
            with response:
                record['http_status'] = response.status
                limit = 65536 if auth else 1048576
                raw = response.read(limit + 1)
                record['response_bytes'] = len(raw)
                if response.status != expected:
                    raise Stop('unexpected_status')
                if len(raw) > limit:
                    raise Stop('response_size')
                data = json.loads(raw)
                if auth and expected == 200:
                    if not isinstance(data, dict) or not isinstance(data.get('id'), str) or not data['id']:
                        raise Stop('identity_shape')
                    record['identity_present'] = True
                    return None  # Do not retain user profile after validating shape/status.
                return data
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)
            record['elapsed_ms'] = round((time.monotonic() - start) * 1000)

    try:
        read('real_key_session', '/auth/session', auth=True)
        read('synthetic_invalid_session', '/auth/session', credential='SYNTHETIC-INVALID-NOT-A-REAL-KEY', expected=401, auth=True)
        read('missing_key_session', '/auth/session', credential=None, expected=401, auth=True)
        checks.append({'check': 'documented_auth_session_accepts_real_rejects_invalid_missing', 'outcome': 'Pass'})
        categories = read('external_categories', '/external-categories', charge=2)
        if not isinstance(categories, list):
            raise Stop('category_shape')
        isbn_categories = [c for c in categories if isinstance(c, dict) and 'isbn' in str(c.get('title', '')).casefold()]
        checks.append({'check': 'isbn_category_observation', 'outcome': 'Recorded',
                       'category_count': len(categories), 'isbn_named_category_count': len(isbn_categories),
                       'limitation': 'Name observation and declared schema only; no guessed ISBN lookup.'})
        path_start = time.monotonic()
        read('cold_session', '/auth/session', auth=True)
        hits = read('cold_search', '/search', body={'q': 'the martian', 'type': 'books'}, charge=3)
        if not isinstance(hits, list) or not 1 <= len(hits) <= 10:
            raise Stop('search_shape')
        books = []
        for hit in hits[:2]:
            book_id = hit.get('id')
            if not isinstance(book_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', book_id):
                raise Stop('book_id_shape')
            book = read('cold_book_' + str(len(books)+1), '/books/' + book_id)
            if not isinstance(book, dict) or not isinstance(book.get('releases', []), list):
                raise Stop('book_shape')
            books.append(book)
        # Round-robin finalists preserve recordings from both selected works.
        candidates = []
        for index in range(max(len(book.get('releases', [])) for book in books)):
            for book in books:
                releases = book.get('releases', [])
                if index < len(releases):
                    candidates.append((book, releases[index]))
            if len(candidates) >= 6:
                break
        mapped, seen = [], set()
        for book, summary in candidates[:6]:
            release_id = summary.get('id')
            if not isinstance(release_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', release_id):
                raise Stop('release_id_shape')
            if release_id in seen:
                continue
            seen.add(release_id)
            detail = read('cold_release_' + str(len(seen)), '/releases/' + release_id)
            if not isinstance(detail, dict) or detail.get('book', {}).get('id') != book['id']:
                raise Stop('release_book_mismatch')
            mapped.append(mapper.map_release(book, detail))
        duration = time.monotonic() - path_start
        if duration >= 8 or not mapped:
            raise Stop('cold_acceptance')
        checks.append({'check': 'bounded_cold_pipeline', 'outcome': 'Pass', 'elapsed_ms': round(duration*1000),
                       'attempts': path_calls, 'documented_cost_cap': path_cost,
                       'selected_books': len(books), 'expanded_releases': len(seen), 'match_count': len(mapped),
                       'observed_upstream_concurrency': 1, 'note': 'Sequential fixture run; global concurrency policy tested separately.'})
        path_start = None
        warm_start = time.monotonic()
        read('warm_session', '/auth/session', auth=True)
        assert len(mapped) == len(seen)  # Touch transient payload only after fresh auth.
        warm = time.monotonic() - warm_start
        if warm >= 8:
            raise Stop('warm_deadline')
        checks.append({'check': 'warm_reuse_after_fresh_auth', 'outcome': 'Pass',
                       'elapsed_ms': round(warm*1000), 'upstream_attempts': 1, 'documented_cost_cap': 1})
        outcome = 'Pass'
    except Exception as error:
        reason = str(error) if isinstance(error, Stop) else type(error).__name__
    finally:
        folder = ROOT / 'docs/evidence/SPIKE-006'
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        result = {'captured_at_utc': stamp, 'classification': 'live_read_only_auth_and_bounded_pipeline',
                  'python_version': platform.python_version(), 'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'outcome': outcome, 'stop_reason': reason, 'attempted_calls': calls,
                  'documented_cost_cap': cost, 'checks': checks, 'requests': records,
                  'limitations': 'One fixture run only; real key never revoked; warm reuse is transient memory, not production cache; ISBN resolver unverified.'}
        encoded = json.dumps(result, indent=2)
        assert key not in encoded and 'SYNTHETIC-INVALID-NOT-A-REAL-KEY' not in encoded
        target = folder / ('finalization-' + stamp + '.json')
        with target.open('x') as output:
            output.write(encoded + '\n')
        print('Finalization probe: ' + outcome + '. Evidence: ' + str(target.relative_to(ROOT)))
    return 0 if outcome == 'Pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
