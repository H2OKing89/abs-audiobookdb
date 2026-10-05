"""Synthetic local provider; do not deploy or point production ABS at this."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

lock = threading.Lock()
state = {'delay': 0, 'status': 200, 'malformed': False, 'expected_auth': 'SYNTHETIC-SPIKE-AUTH'}
captures = []
matches = json.loads(Path('/lab/matches.json').read_text())


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, status, payload):
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        if status == 429:
            self.send_header('Retry-After', '1')
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        if self.path != '/control':
            return self.send_json(404, {})
        length = int(self.headers.get('Content-Length', 0))
        if not 0 < length <= 4096:
            return self.send_json(400, {})
        update = json.loads(self.rfile.read(length))
        with lock:
            state.update(update)
        self.send_json(200, {'configured': True})

    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path == '/captures':
            with lock:
                result = list(captures)
            return self.send_json(200, result)
        if parsed.path != '/search':
            return self.send_json(404, {})
        params = parse_qs(parsed.query)
        with lock:
            current = dict(state)
            captures.append({'method': 'GET', 'query_keys': sorted(params),
                             'media_type': params.get('mediaType', [None])[0],
                             'auth_matches_expected': self.headers.get('Authorization') == current['expected_auth'],
                             'delay_seconds': current['delay'], 'fixture_status': current['status']})
        time.sleep(current['delay'])
        if self.headers.get('Authorization') != current['expected_auth']:
            return self.send_json(401, {'error': 'synthetic authorization rejected'})
        payload = {} if current['malformed'] else {'matches': matches}
        if current['status'] != 200:
            payload = {'error': 'synthetic provider failure'}
        self.send_json(current['status'], payload)


ThreadingHTTPServer(('0.0.0.0', 8000), Handler).serve_forever()
