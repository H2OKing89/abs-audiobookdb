#!/usr/bin/env python3
"""Publish a verified local release, then promote its public image to latest."""
import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'ghcr.io/h2oking89/abs-audiobookdb'
SOURCE = 'https://github.com/H2OKing89/abs-audiobookdb'
VERSION = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)')


def command(*args, env=None):
    return subprocess.run(args, cwd=ROOT, env=env, check=True,
                          capture_output=True, text=True).stdout.strip()


def artifacts(version):
    if not VERSION.fullmatch(version):
        raise ValueError('Use a release version such as 0.1.0, without v or prerelease suffixes.')
    directory = ROOT / 'dist' / f'v{version}'
    archive = directory / f'abs-audiobookdb-{version}-linux-amd64-image.tar.gz'
    required = {archive.name, 'image-id.txt', 'version.json', 'load.json'}
    checked = set()
    for line in (directory / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        name = name.lstrip(' *')
        if Path(name).name != name or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError('Invalid release checksum entry.')
        with (directory / name).open('rb') as stream:
            checksum = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                checksum.update(chunk)
            actual = checksum.hexdigest()
        if actual != digest:
            raise ValueError(f'Release checksum mismatch: {name}')
        checked.add(name)
    if not required.issubset(checked):
        raise ValueError('Required release artifacts are missing from SHA256SUMS.')
    identity = json.loads((directory / 'version.json').read_text())
    image = (directory / 'image-id.txt').read_text().strip()
    load = json.loads((directory / 'load.json').read_text())
    revision = command('git', 'rev-list', '-n', '1', f'v{version}')
    expected = {'version': version, 'revision': revision, 'dirty': 'false'}
    if identity != expected or not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Release identity must match its immutable Git tag and a clean build.')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
        raise ValueError('Invalid release image ID.')
    if (load.get('outcome') != 'Pass' or load.get('stage') != 'complete'
            or load.get('image_id') != image or load.get('build') != identity
            or load.get('memory', {}).get('oom_killed') is not False
            or load.get('memory', {}).get('restarts') != 0):
        raise ValueError('Release load report must pass for this exact clean image.')
    return archive, image, identity


def verify_image(image, identity):
    info = json.loads(command('docker', 'image', 'inspect', image))[0]
    labels = info['Config'].get('Labels', {})
    if (info['Id'] != image or info['Os'] != 'linux' or info['Architecture'] != 'amd64'
            or labels.get('org.opencontainers.image.version') != identity['version']
            or labels.get('org.opencontainers.image.revision') != identity['revision']
            or labels.get('org.opencontainers.image.source') != SOURCE):
        raise ValueError('Image platform or OCI identity does not match the release.')
    observed = json.loads(command('docker', 'run', '--rm', '--network', 'none', image, 'version'))
    if observed != identity:
        raise ValueError('Executable identity does not match the release.')


def package_is_missing():
    """Resolve GHCR's ambiguous denied response for a package's first publication."""
    config_path = Path(os.environ.get('DOCKER_CONFIG', str(Path.home() / '.docker'))) / 'config.json'
    config = json.loads(config_path.read_text())
    helper = config.get('credHelpers', {}).get('ghcr.io') or config.get('credsStore')
    if helper:
        result = subprocess.run([f'docker-credential-{helper}', 'get'], input='ghcr.io\n',
                                check=True, capture_output=True, text=True)
        token = json.loads(result.stdout)['Secret']
    else:
        auth = config.get('auths', {}).get('ghcr.io', {}).get('auth', '')
        token = base64.b64decode(auth, validate=True).decode().split(':', 1)[1]

    def request(path):
        return urllib.request.urlopen(urllib.request.Request(
            'https://api.github.com' + path,
            headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                     'User-Agent': 'abs-audiobookdb-local-publisher'}), timeout=15)

    with request('/user') as response:
        owner = json.load(response).get('login', '').lower()
        scopes = {scope.strip() for scope in response.headers.get('X-OAuth-Scopes', '').split(',')}
    if owner != 'h2oking89' or 'write:packages' not in scopes:
        raise ValueError('GHCR needs the owner classic token with write:packages; existing tags were not changed.')
    try:
        with request('/user/packages/container/abs-audiobookdb'):
            return False
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return True
        raise


def pull_existing(reference, env=None):
    result = subprocess.run(['docker', 'pull', reference], cwd=ROOT, env=env,
                            capture_output=True, text=True)
    if result.returncode == 0:
        return command('docker', 'image', 'inspect', '--format', '{{.Id}}', reference, env=env)
    if 'manifest unknown' in result.stderr.lower():
        return None
    if env is None:
        try:
            if package_is_missing():
                return None
        except (OSError, ValueError, KeyError, IndexError, subprocess.CalledProcessError):
            pass
    raise ValueError(f'Cannot check {reference}: authentication or registry access failed. No tag was overwritten.')


def publish(image, identity):
    reference = f'{REPOSITORY}:{identity["version"]}'
    existing = pull_existing(reference)
    if existing is not None and existing != image:
        raise ValueError('Version tag already contains a different image; version tags are never overwritten.')
    if existing is None:
        command('docker', 'tag', image, reference)
        print(f'Publishing {reference}...', flush=True)
        command('docker', 'push', reference)
    if pull_existing(reference) != image:
        raise ValueError('Published version tag does not match the verified image.')
    # An empty Docker config prevents a saved login/helper from masking private visibility.
    with tempfile.TemporaryDirectory(prefix='abs-anonymous-pull-') as config:
        env = dict(os.environ, DOCKER_CONFIG=config)
        env.pop('DOCKER_AUTH_CONFIG', None)
        try:
            if pull_existing(reference, env=env) != image:
                raise ValueError('Anonymous version pull returned a different image.')
        except ValueError as error:
            raise ValueError('Version image is not publicly pullable. Make the package public at '
                             'https://github.com/users/H2OKing89/packages/container/abs-audiobookdb/settings '
                             'and rerun; latest has not been changed.') from error
        latest = f'{REPOSITORY}:latest'
        current = pull_existing(latest, env=env)
        if current is not None:
            label = command('docker', 'image', 'inspect', '--format',
                            '{{index .Config.Labels "org.opencontainers.image.version"}}', current)
            if not VERSION.fullmatch(label):
                raise ValueError('Existing latest image has no valid release version; refusing promotion.')
            if tuple(map(int, label.split('.'))) > tuple(map(int, identity['version'].split('.'))):
                raise ValueError('Refusing to replace latest with an older release.')
        command('docker', 'tag', image, latest)
        print(f'Promoting {reference} to latest...', flush=True)
        command('docker', 'push', latest)
        if pull_existing(latest, env=env) != image:
            raise ValueError('Anonymous latest pull does not match the verified image.')
    print(f'Public version and latest tags verified: {image}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version', help='Packaged release version, such as 0.1.0')
    parser.add_argument('--verify-only', action='store_true', help='Verify local artifacts/image without publishing')
    args = parser.parse_args()
    try:
        archive, image, identity = artifacts(args.version)
        command('docker', 'load', '-i', str(archive))
        verify_image(image, identity)
        print(f'Verified local release {args.version}: {image}', flush=True)
        if not args.verify_only:
            publish(image, identity)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        # Avoid forwarding authenticated command output into logs.
        detail = str(error) if not isinstance(error, subprocess.CalledProcessError) else 'A Git/Docker command failed; check local login and service availability.'
        parser.exit(1, detail + '\n')


if __name__ == '__main__':
    main()
