#!/usr/bin/env python3
"""TLS synthetic upstream for delivered-adapter acceptance; no outbound access."""
import json
import ssl
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

data = json.loads(Path('/lab/data.json').read_text())
lock = threading.Lock()
state = {'reject': False, 'calls': 0}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, status, body):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_POST(self):
        length = int(self.headers.get('Content-Length', '0'))
        if length > 8192:
            return self.send(413, {})
        body = json.loads(self.rfile.read(length) or b'{}')
        if self.path == '/control':
            with lock:
                state['reject'] = bool(body.get('reject'))
            return self.send(200, {})
        if self.path == '/api/search':
            return self.respond()
        self.send(404, {})

    def do_GET(self):
        if self.path == '/stats':
            with lock:
                count = state['calls']
            return self.send(200, {'calls': count})
        self.respond()

    def respond(self):
        with lock:
            state['calls'] += 1
            reject = state['reject']
        if reject or self.headers.get('X-API-Key') != 'SYNTHETIC-MVP-KEY':
            return self.send(401, {'error': 'synthetic'})
        if self.path == '/api/auth/session':
            return self.send(200, {'id': 'invented-account'})
        if self.path == '/api/search':
            return self.send(200, [{'id': data['book']['id'], 'title': data['book']['title'],
                                    'genres': ['Synthetic Genre'], 'tags': ['Synthetic Tag'],
                                    'series': ['Synthetic Series']}])
        if self.path == '/api/books/' + data['book']['id']:
            return self.send(200, data['book'])
        for release in data['releases']:
            if self.path == '/api/releases/' + release['id']:
                return self.send(200, release)
        self.send(404, {})


server = ThreadingHTTPServer(('0.0.0.0', 8443), Handler)
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('/lab/cert.pem', '/lab/key.pem')
server.socket = context.wrap_socket(server.socket, server_side=True)
server.serve_forever()
