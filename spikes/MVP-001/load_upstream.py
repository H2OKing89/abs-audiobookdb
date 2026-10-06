"""Invented large-response HTTPS upstream for the isolated memory experiment."""
import hashlib
import json
import ssl
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LOCK = threading.Lock()
CALLS = 0
BOOKS = {}
PADDED_BYTES = 900 * 1024


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, status, body, padded=False):
        if padded:
            body['padding'] = ''
            size = len(json.dumps(body).encode())
            body['padding'] = 'x' * max(0, PADDED_BYTES - size)
        raw = json.dumps(body).encode()
        try:
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        self.dispatch()

    def do_POST(self):
        self.dispatch()

    def dispatch(self):
        global CALLS
        if self.path == '/stats':
            with LOCK:
                calls = CALLS
            self.send(200, {'calls': calls})
            return
        with LOCK:
            CALLS += 1
        if self.headers.get('X-API-Key') != 'SYNTHETIC-LOAD-KEY':
            self.send(401, {})
            return
        if self.path == '/api/auth/session':
            self.send(200, {'id': 'synthetic-load-account'})
        elif self.path == '/api/search':
            request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            query = request['q']
            prefix = hashlib.sha256(query.encode()).hexdigest()[:20]
            ids = [prefix + '_1', prefix + '_2']
            with LOCK:
                for identity in ids:
                    BOOKS[identity] = query
            self.send(200, [{'id': identity, 'title': query} for identity in ids])
        elif self.path.startswith('/api/books/'):
            identity = self.path.rsplit('/', 1)[1]
            with LOCK:
                query = BOOKS[identity]
            if query == 'Synthetic slow response':
                time.sleep(2.25)
            if query == 'Synthetic oversized response':
                self.send(200, {'id': identity, 'title': query, 'padding': 'x' * (1024 * 1024)})
                return
            description_bytes = 200 * 1024 if query == 'Synthetic oversized mapping' else 60 * 1024
            self.send(200, {
                'id': identity, 'title': query, 'description': 'd' * description_bytes,
                'people': [{'person': {'name': 'Invented Author'}, 'role': {'name': 'Author'}}],
                'releases': [{'id': identity + '_r' + str(n)} for n in range(3)],
            }, padded=True)
        elif self.path.startswith('/api/releases/'):
            identity = self.path.rsplit('/', 1)[1]
            book = identity.rsplit('_r', 1)[0]
            self.send(200, {
                'id': identity, 'book': {'id': book}, 'title': 'Invented Recording',
                'language': {'name': 'English'}, 'runtimeLengthMs': 600000,
                'people': [{'person': {'name': 'Invented Narrator'}, 'role': {'name': 'Narrator'}}],
            }, padded=True)
        else:
            self.send(404, {})


if __name__ == '__main__':
    server = ThreadingHTTPServer(('0.0.0.0', 8443), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('/lab/cert.pem', '/lab/key.pem')
    server.socket = context.wrap_socket(server.socket, server_side=True)
    server.serve_forever()
