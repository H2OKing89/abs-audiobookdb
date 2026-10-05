#!/usr/bin/env python3
"""Disposable delivered image on existing Unraid network; no API calls."""
import argparse
import datetime
import hashlib
import io
import json
import secrets
import shlex
import shutil
import ssl
import subprocess
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = 'abs-audiobookdb:mvp-20261005'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', required=True)
    args = parser.parse_args()
    project = 'abs-mvp-deploy-' + secrets.token_hex(4)
    image = project + ':private'
    lab = Path(tempfile.mkdtemp(prefix=project))
    remote_lab = ''
    checks, cleanup, versions = [], [], {}
    outcome, reason, stage = 'Incomplete', None, 'prepare'
    image_id = subprocess.run(['docker', 'image', 'inspect', IMAGE, '--format', '{{.Id}}'], capture_output=True, text=True, check=True).stdout.strip()

    def ssh(command, input_bytes=None, check=True):
        return subprocess.run(['ssh', '-oBatchMode=yes', '-oConnectTimeout=5', '-oStrictHostKeyChecking=yes', args.target, command], input=input_bytes, capture_output=True, timeout=90, check=check)

    def cmd(*words, check=True):
        return ssh(shlex.join(words), check=check)

    def compose(*words, check=True):
        return cmd('docker', 'compose', '-p', project, '-f', remote_lab + '/compose.json', *words, check=check)

    try:
        stage = 'inventory'
        versions = {'docker': cmd('docker', 'version', '--format', '{{.Server.Version}}').stdout.decode().strip(), 'compose': cmd('docker', 'compose', 'version', '--short').stdout.decode().strip()}
        assert cmd('docker', 'network', 'inspect', 'proxynet', '--format', '{{.Driver}}').stdout.decode().strip() == 'bridge'
        remote_lab = ssh('mktemp -d /tmp/' + project + '-XXXXXX').stdout.decode().strip()
        assert remote_lab.startswith('/tmp/' + project + '-') and '\n' not in remote_lab
        # The target IP is used only in transient configuration, never archived.
        address = args.target.rsplit('@', 1)[-1]
        names = {n: project + '-' + n for n in ('http', 'native', 'badkey')}
        certs = lab / 'certs'; certs.mkdir()
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1', '-subj', '/CN=synthetic-target.invalid', '-addext',
                        'subjectAltName=DNS:' + names['native'] + ',IP:127.0.0.1,IP:' + address,
                        '-keyout', str(certs / 'key.pem'), '-out', str(certs / 'cert.pem')], capture_output=True, check=True)
        shutil.copyfile(certs / 'key.pem', certs / 'unreadable.pem')
        (certs / 'key.pem').chmod(0o640); (certs / 'unreadable.pem').chmod(0o600)
        config = {'services': {}, 'networks': {'shared': {'external': True, 'name': 'proxynet'}}}
        for mode in ('http', 'native'):
            environment = {'AUDIOBOOKDB_CONTACT': 'operator@example.invalid', 'GOMEMLIMIT': '192MiB'}
            if mode == 'native':
                environment.update(TLS_CERT_FILE='/certs/cert.pem', TLS_KEY_FILE='/certs/key.pem', HEALTH_CA_FILE='/certs/cert.pem')
            ports = ['127.0.0.1::8080', address + '::8080'] if mode == 'http' else [address + '::8080']
            config['services'][names[mode]] = {'image': image, 'user': '99:100', 'read_only': True, 'cap_drop': ['ALL'], 'security_opt': ['no-new-privileges:true'], 'mem_limit': '256m', 'environment': environment, 'volumes': ['./certs:/certs:ro'], 'networks': ['shared'], 'ports': ports}
        (lab / 'compose.json').write_text(json.dumps(config))
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode='w:gz') as tar:
            for child in lab.iterdir():
                tar.add(child, arcname=child.name)
        ssh('tar -xz -C ' + shlex.quote(remote_lab), input_bytes=archive.getvalue())
        cmd('chown', '-R', '0:100', remote_lab + '/certs')
        stage = 'image-transfer'
        # Import under a unique temporary tag, preserving any existing target tag.
        # A docker-save archive is retagged before transfer, avoiding target collisions.
        unique = project + ':transfer'
        subprocess.run(['docker', 'tag', IMAGE, unique], check=True, capture_output=True)
        try:
            image_data = subprocess.run(['docker', 'save', unique], capture_output=True, check=True, timeout=60).stdout
            ssh('docker load', input_bytes=image_data)
            cmd('docker', 'tag', unique, image)
            assert cmd('docker', 'image', 'inspect', image, '--format', '{{.Id}}').stdout.decode().strip() == image_id
            cmd('docker', 'image', 'rm', unique)
        finally:
            subprocess.run(['docker', 'image', 'rm', unique], capture_output=True)
        stage = 'startup'; compose('up', '-d')
        for mode in ('http', 'native'):
            for _ in range(20):
                if compose('exec', '-T', names[mode], '/adapter', 'health', check=False).returncode == 0:
                    break
                time.sleep(0.25)
            else:
                raise RuntimeError('health')
            cid = compose('ps', '-q', names[mode]).stdout.decode().strip()
            assert cmd('docker', 'inspect', cid, '--format', '{{.Config.User}}').stdout.decode().strip() == '99:100'
            assert cmd('docker', 'inspect', cid, '--format', '{{.HostConfig.Memory}}').stdout.decode().strip() == str(256 << 20)
            binding = json.loads(cmd('docker', 'inspect', cid, '--format', '{{json .NetworkSettings.Ports}}').stdout)
            host = '127.0.0.1' if mode == 'http' else address
            port = next(b['HostPort'] for b in binding['8080/tcp'] if b['HostIp'] == host)
            words = ['curl', '--fail', '--silent', '--show-error', '--max-time', '3']
            if mode == 'native':
                words += ['--cacert', remote_lab + '/certs/cert.pem']
            url = ('http://' if mode == 'http' else 'https://') + host + ':' + port + '/health'
            assert b'"ok"' in cmd(*words, url).stdout
            if mode == 'native':
                trust = ssl.create_default_context(cafile=str(certs / 'cert.pem'))
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=trust))
                with opener.open(url, timeout=3) as response:
                    assert response.status == 200 and json.loads(response.read(1024))['status'] == 'ok'
            else:
                lan_port = next(b['HostPort'] for b in binding['8080/tcp'] if b['HostIp'] == address)
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                with opener.open('http://' + address + ':' + lan_port + '/health', timeout=3) as response:
                    assert response.status == 200 and json.loads(response.read(1024))['status'] == 'ok'
            # Verify actual adapter reachability from a second container on proxynet.
            env = ['-e', 'LISTEN_ADDR=' + names[mode] + ':8080', '-e', 'AUDIOBOOKDB_CONTACT=operator@example.invalid']
            if mode == 'native':
                env += ['-e', 'TLS_CERT_FILE=/certs/cert.pem', '-e', 'HEALTH_CA_FILE=/certs/cert.pem']
            cmd('docker', 'run', '--rm', '--network', 'proxynet', '--mount', 'type=bind,src=' + remote_lab + '/certs,dst=/certs,readonly', *env, image, 'health')
            checks.append({'check': mode + '_99_100_memory_health_shared_network_and_binding', 'outcome': 'Pass', 'binding': 'loopback_and_private_lan' if mode == 'http' else 'private_lan'})
        stage = 'tls-negatives'
        assert compose('exec', '-T', '-e', 'HEALTH_CA_FILE=', names['native'], '/adapter', 'health', check=False).returncode != 0
        assert compose('exec', '-T', '-e', 'LISTEN_ADDR=localhost:8080', names['native'], '/adapter', 'health', check=False).returncode != 0
        negative = cmd('docker', 'run', '--name', names['badkey'], '--network', 'none', '--read-only', '-e', 'AUDIOBOOKDB_CONTACT=operator@example.invalid', '-e', 'TLS_CERT_FILE=/certs/cert.pem', '-e', 'TLS_KEY_FILE=/certs/unreadable.pem', '--mount', 'type=bind,src=' + remote_lab + '/certs,dst=/certs,readonly', image, check=False)
        assert negative.returncode != 0
        checks.append({'check': 'untrusted_tls_wrong_san_unreadable_key_rejected', 'outcome': 'Pass'})
        stage = 'shutdown'; start = time.monotonic(); compose('stop', '-t', '10'); elapsed = time.monotonic() - start
        assert elapsed < 10
        for mode in ('http', 'native'):
            cid = compose('ps', '-a', '-q', names[mode]).stdout.decode().strip()
            assert cmd('docker', 'inspect', cid, '--format', '{{.State.ExitCode}}').stdout.decode().strip() == '0'
        checks.append({'check': 'both_graceful_shutdown_exit_zero', 'outcome': 'Pass', 'seconds': round(elapsed, 3)})
        outcome = 'Pass'
    except Exception as error:
        reason = type(error).__name__
    finally:
        if remote_lab:
            for resource, action in [('project', lambda: compose('down', check=False)), ('negative', lambda: cmd('docker', 'rm', '-f', project + '-badkey', check=False)), ('image', lambda: cmd('docker', 'image', 'rm', image, check=False)), ('transfer_tag', lambda: cmd('docker', 'image', 'rm', project + ':transfer', check=False)), ('remote_lab', lambda: cmd('rm', '-rf', '--', remote_lab, check=False))]:
                try:
                    result = action(); cleanup.append({'resource': resource, 'removed': result.returncode == 0, 'note': 'Nonzero can mean never created or already removed.'})
                except Exception:
                    cleanup.append({'resource': resource, 'removed': False})
        shutil.rmtree(lab)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        folder = ROOT / 'docs/evidence/MVP-001'; folder.mkdir(parents=True, exist_ok=True)
        record = {'captured_at_utc': stamp, 'classification': 'delivered_adapter_live_unraid_disposable_project', 'outcome': outcome, 'stage': stage, 'stop_reason': reason, 'versions': versions, 'checks': checks, 'cleanup': cleanup, 'image_id': image_id, 'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'limitations': 'Actual Unraid host, temporary project only; no existing projects or live ABS configured. HTTP and native TLS LAN listeners also checked from development machine. No upstream API calls or reverse proxy.'}
        target = folder / ('deployment-' + stamp + '.json'); target.write_text(json.dumps(record, indent=2) + '\n')
        print('Delivered Unraid deployment: ' + outcome + ' at ' + stage + '. Evidence: ' + str(target.relative_to(ROOT)))
    return 0 if outcome == 'Pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
