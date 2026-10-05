#!/usr/bin/env python3
"""Bounded throwaway deployment checks; never changes existing projects."""
import argparse
import datetime
import hashlib
import io
import json
import os
import secrets
import shlex
import shutil
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--local', action='store_true')
    choice.add_argument('--target', help='SSH target with an already authenticated session')
    args = parser.parse_args()
    project = 'abs-deploy-' + secrets.token_hex(4)
    image = project + ':fixture'
    lab = Path(tempfile.mkdtemp(prefix=project + '-'))
    target_lab = str(lab)
    uploaded = False
    checks, cleanup = [], []
    outcome, reason = 'Incomplete', None
    started = time.monotonic()

    def run(command, *, input_bytes=None, check=True, timeout=90, cwd=None):
        return subprocess.run(command, input=input_bytes, capture_output=True,
                              check=check, timeout=timeout, cwd=cwd)

    def target(command, *, input_bytes=None, check=True):
        if args.local:
            return run(['sh', '-c', command], input_bytes=input_bytes, check=check)
        return run(['ssh', '-oBatchMode=yes', '-oConnectTimeout=5', '-oStrictHostKeyChecking=yes',
                    args.target, command], input_bytes=input_bytes, check=check)

    def compose(*command, check=True):
        base = ['docker', 'compose', '-p', project, '-f', target_lab + '/compose.json']
        return target(shlex.join(base + list(command)), check=check)

    try:
        env = dict(os.environ, CGO_ENABLED='0', GOOS='linux', GOARCH='amd64')
        subprocess.run(['go', 'build', '-trimpath', '-o', str(lab / 'health'), '.'],
                       cwd=HERE, env=env, capture_output=True, check=True, timeout=90)
        shutil.copyfile(HERE / 'Dockerfile', lab / 'Dockerfile')
        certs = lab / 'certs'
        certs.mkdir(mode=0o755)
        names = {mode: project + '-' + mode for mode in ('http', 'native', 'proxy', 'unreadable')}
        run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
             '-subj', '/CN=synthetic-deployment-fixture.invalid', '-addext',
             'subjectAltName=DNS:' + names['native'] + ',DNS:' + names['proxy'],
             '-keyout', str(certs / 'key.pem'), '-out', str(certs / 'cert.pem')])
        shutil.copyfile(certs / 'key.pem', certs / 'unreadable.pem')
        (certs / 'key.pem').chmod(0o640)
        (certs / 'unreadable.pem').chmod(0o600)
        if args.local:
            os.chown(certs / 'key.pem', -1, 100)
        else:
            target_lab = target('mktemp -d /tmp/' + project + '-XXXXXX').stdout.decode().strip()
            assert target_lab.startswith('/tmp/' + project + '-') and '\n' not in target_lab
            uploaded = True
        network = {'driver': 'bridge', 'internal': True} if args.local else {'external': True, 'name': 'proxynet'}
        service_base = {'image': image, 'user': '99:100', 'read_only': True, 'tmpfs': ['/tmp'],
                        'networks': ['fixture'], 'volumes': ['./certs:/certs:ro'], 'labels': {'abs.spike': project}}
        config = {'services': {}, 'networks': {'fixture': network}}
        for mode in ('http', 'native', 'proxy'):
            service = dict(service_base)
            command = ['-listen', ':8080']
            if mode != 'http':
                command = ['-listen', ':8443', '-cert', '/certs/cert.pem', '-key', '/certs/key.pem']
            if mode == 'proxy':
                command += ['-upstream', 'http://' + names['http'] + ':8080']
            service['command'] = command
            config['services'][names[mode]] = service
        (lab / 'compose.json').write_text(json.dumps(config))
        if not args.local:
            data = io.BytesIO()
            with tarfile.open(fileobj=data, mode='w:gz') as archive:
                for child in lab.iterdir():
                    archive.add(child, arcname=child.name)
            target('tar -xz -C ' + shlex.quote(target_lab), input_bytes=data.getvalue())
            target('chown -R 0:100 ' + shlex.quote(target_lab + '/certs'))
            target('docker network inspect proxynet --format {{.Driver}}')
        versions = {'docker': target("docker version --format '{{.Server.Version}}'").stdout.decode().strip(),
                    'compose': target('docker compose version --short').stdout.decode().strip()}
        target(shlex.join(['docker', 'build', '-t', image, target_lab]))
        compose('up', '-d')

        def probe(mode, ca=True, host=None, check=True):
            url = ('http://' if mode == 'http' else 'https://') + (host or names[mode]) + (':8080' if mode == 'http' else ':8443') + '/healthz'
            command = ['exec', '-T', names['http'], '/health', '-probe', url]
            if mode != 'http' and ca:
                command += ['-ca', '/certs/cert.pem']
            return compose(*command, check=check)

        for mode in ('http', 'native', 'proxy'):
            for _ in range(4):
                if probe(mode, check=False).returncode == 0:
                    break
                time.sleep(0.25)
            else:
                raise RuntimeError('fixture_health_not_ready')
            for _ in range(3):
                assert probe(mode).stdout.decode().strip() == 'health_pass uid=99 gid=100'
            checks.append({'check': mode + '_health_identity_trust', 'outcome': 'Pass', 'recorded_successes': 3})
        untrusted = probe('native', ca=False, check=False)
        assert untrusted.returncode != 0 and b'probe_authority_failed' in untrusted.stderr
        checks.append({'check': 'untrusted_tls_rejected', 'outcome': 'Pass'})
        # The same native endpoint's IP is deliberately absent from certificate SANs.
        container_id = compose('ps', '-q', names['native']).stdout.decode().strip()
        native_ip = target(shlex.join(['docker', 'inspect', container_id, '--format', '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'])).stdout.decode().strip()
        wrong_hostname = probe('native', host=native_ip, check=False)
        assert wrong_hostname.returncode != 0 and b'probe_hostname_failed' in wrong_hostname.stderr
        checks.append({'check': 'wrong_certificate_hostname_rejected', 'outcome': 'Pass'})
        stop_start = time.monotonic()
        compose('stop', '-t', '10')
        elapsed = time.monotonic() - stop_start
        assert elapsed < 10
        for mode in ('http', 'native', 'proxy'):
            cid = compose('ps', '-a', '-q', names[mode]).stdout.decode().strip()
            state = target(shlex.join(['docker', 'inspect', cid, '--format', '{{.State.ExitCode}}'])).stdout.decode().strip()
            assert state == '0'
        checks.append({'check': 'graceful_stop', 'outcome': 'Pass', 'seconds': round(elapsed, 3), 'all_exit_codes_zero': True})
        negative = target(shlex.join(['docker', 'run', '--name', names['unreadable'], '--label', 'abs.spike=' + project,
                                      '--network', 'none', '--read-only', '--mount', 'type=bind,src=' + target_lab + '/certs,dst=/certs,readonly',
                                      image, '-cert', '/certs/cert.pem', '-key', '/certs/unreadable.pem']), check=False)
        assert negative.returncode != 0 and b'fixture_start_failed' in negative.stderr
        checks.append({'check': 'unreadable_key_startup_rejected', 'outcome': 'Pass'})
        assert time.monotonic() - started < 600
        outcome = 'Pass'
    except Exception as error:
        reason = type(error).__name__
        versions = locals().get('versions', {})
    finally:
        for label, command in [('compose_project', ['docker', 'compose', '-p', project, '-f', target_lab + '/compose.json', 'down']),
                               ('negative_container', ['docker', 'rm', '-f', project + '-unreadable']),
                               ('fixture_image', ['docker', 'image', 'rm', image])]:
            try:
                result = target(shlex.join(command), check=False)
                cleanup.append({'resource': label, 'removed': result.returncode == 0,
                                'note': 'A nonzero removal may mean the resource was never created.'})
            except Exception:
                cleanup.append({'resource': label, 'removed': False})
        if uploaded:
            try:
                target('rm -rf -- ' + shlex.quote(target_lab))
                cleanup.append({'resource': 'temporary_remote_directory', 'removed': True})
            except Exception:
                cleanup.append({'resource': 'temporary_remote_directory', 'removed': False})
        shutil.rmtree(lab, ignore_errors=True)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        folder = ROOT / 'docs/evidence/SPIKE-005'
        folder.mkdir(parents=True, exist_ok=True)
        record = {'captured_at_utc': stamp, 'classification': 'local_docker_fixture' if args.local else 'target_unraid_fixture',
                  'outcome': outcome, 'stop_reason': reason, 'versions': versions, 'checks': checks, 'cleanup': cleanup,
                  'source_sha256': hashlib.sha256((HERE / 'main.go').read_bytes()).hexdigest(),
                  'limitations': 'Generic TLS reverse proxy only, not existing SWAG configuration. Local checks do not establish Unraid/proxynet compatibility.'}
        output = folder / ('deployment-' + stamp + '.json')
        output.write_text(json.dumps(record, indent=2) + '\n')
        print('Deployment outcome: ' + outcome + '. Evidence: ' + str(output.relative_to(ROOT)))
    return 0 if outcome == 'Pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
