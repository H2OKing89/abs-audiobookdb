"""Protect immutable release tags and the public latest promotion boundary."""
import hashlib
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
from unittest.mock import Mock

import publish_image as publisher

IMAGE = 'sha256:' + '1' * 64
IDENTITY = {'version': '0.1.0', 'revision': 'a' * 40, 'dirty': 'false'}


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.directory = self.root / 'dist/v0.1.0'
        self.directory.mkdir(parents=True)
        self.load = {'outcome': 'Pass', 'stage': 'complete', 'image_id': IMAGE,
                     'build': IDENTITY, 'memory': {'oom_killed': False, 'restarts': 0}}
        (self.directory / 'abs-audiobookdb-0.1.0-linux-amd64-image.tar.gz').write_bytes(b'fixture archive')
        (self.directory / 'image-id.txt').write_text(IMAGE)
        self.write_reports()
        root_patch = patch.object(publisher, 'ROOT', self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)
        command_patch = patch.object(publisher, 'command', return_value=IDENTITY['revision'])
        command_patch.start()
        self.addCleanup(command_patch.stop)

    def write_reports(self, identity=None):
        (self.directory / 'version.json').write_text(json.dumps(identity or IDENTITY))
        (self.directory / 'load.json').write_text(json.dumps(self.load))
        lines = []
        for path in sorted(self.directory.iterdir()):
            if path.name != 'SHA256SUMS':
                lines.append(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}')
        (self.directory / 'SHA256SUMS').write_text('\n'.join(lines) + '\n')

    def test_verified_release(self):
        _, image, identity = publisher.artifacts('0.1.0')
        self.assertEqual((image, identity), (IMAGE, IDENTITY))

    def test_tampered_archive_rejected(self):
        (self.directory / 'abs-audiobookdb-0.1.0-linux-amd64-image.tar.gz').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            publisher.artifacts('0.1.0')

    def test_dirty_or_wrong_revision_rejected(self):
        for identity in (dict(IDENTITY, dirty='true'), dict(IDENTITY, revision='b' * 40)):
            with self.subTest(identity=identity):
                self.write_reports(identity)
                with self.assertRaisesRegex(ValueError, 'immutable Git tag'):
                    publisher.artifacts('0.1.0')

    def test_failed_or_other_image_load_rejected(self):
        for changes in ({'outcome': 'Fail'}, {'image_id': 'sha256:' + '2' * 64},
                        {'memory': {'oom_killed': True, 'restarts': 0}},
                        {'memory': {'oom_killed': False, 'restarts': 1}}):
            with self.subTest(changes=changes):
                original = self.load.copy()
                self.load.update(changes)
                self.write_reports()
                with self.assertRaisesRegex(ValueError, 'load report'):
                    publisher.artifacts('0.1.0')
                self.load = original

    def test_missing_checksum_or_path_traversal_rejected(self):
        checksums = self.directory / 'SHA256SUMS'
        checksums.write_text('')
        with self.assertRaisesRegex(ValueError, 'missing'):
            publisher.artifacts('0.1.0')
        checksums.write_text('0' * 64 + '  ../outside\n')
        with self.assertRaisesRegex(ValueError, 'Invalid release checksum'):
            publisher.artifacts('0.1.0')

    def test_only_exact_release_versions_accepted(self):
        for version in ('latest', '../outside', 'v0.1.0', '0.1.0-beta', '00.1.0'):
            with self.subTest(version=version), self.assertRaises(ValueError):
                publisher.artifacts(version)


class PromotionTests(unittest.TestCase):
    def setUp(self):
        printing = patch('builtins.print')
        printing.start()
        self.addCleanup(printing.stop)

    @patch.object(publisher, 'command')
    @patch.object(publisher, 'pull_existing', return_value='sha256:' + '2' * 64)
    def test_immutable_version_collision_never_pushes(self, pull, command):
        with self.assertRaisesRegex(ValueError, 'never overwritten'):
            publisher.publish(IMAGE, IDENTITY)
        command.assert_not_called()

    @patch.object(publisher, 'command')
    @patch.object(publisher, 'pull_existing', side_effect=[None, IMAGE, ValueError('private')])
    def test_private_image_never_promoted(self, pull, command):
        with self.assertRaisesRegex(ValueError, 'latest has not been changed'):
            publisher.publish(IMAGE, IDENTITY)
        pushes = [call.args for call in command.call_args_list if call.args[:2] == ('docker', 'push')]
        self.assertEqual(pushes, [('docker', 'push', publisher.REPOSITORY + ':0.1.0')])
        self.assertNotIn('DOCKER_AUTH_CONFIG', pull.call_args.kwargs['env'])

    @patch.object(publisher, 'command', return_value='0.2.0')
    @patch.object(publisher, 'pull_existing', side_effect=[IMAGE, IMAGE, IMAGE, 'sha256:' + '2' * 64])
    def test_older_release_never_replaces_latest(self, pull, command):
        with self.assertRaisesRegex(ValueError, 'older release'):
            publisher.publish(IMAGE, IDENTITY)
        self.assertFalse(any(call.args[:2] == ('docker', 'push') for call in command.call_args_list))

    @patch.object(publisher, 'command')
    @patch.object(publisher, 'pull_existing', side_effect=[None, IMAGE, IMAGE, None, IMAGE])
    def test_public_version_verified_before_latest_push(self, pull, command):
        publisher.publish(IMAGE, IDENTITY)
        pushes = [call.args for call in command.call_args_list if call.args[:2] == ('docker', 'push')]
        self.assertEqual(pushes, [('docker', 'push', publisher.REPOSITORY + ':0.1.0'),
                                  ('docker', 'push', publisher.REPOSITORY + ':latest')])
        self.assertEqual(len(pull.call_args_list), 5)


class RegistryLookupTests(unittest.TestCase):
    def check_owner_lookup(self, owner='H2OKing89', scopes='write:packages', status=404):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        config = Path(temporary.name) / 'config.json'
        config.write_text(json.dumps({'auths': {'ghcr.io': {'auth': 'SDJPS2luZzg5OmludmVudGVkLXRva2Vu'}}}))
        response = io.BytesIO(json.dumps({'login': owner}).encode())
        response.headers = {'X-OAuth-Scopes': scopes}
        error = urllib.error.HTTPError('https://api.github.com/user/packages/container/abs-audiobookdb', status, 'fixture', {}, None)
        return patch.dict(publisher.os.environ, {'DOCKER_CONFIG': temporary.name}), patch.object(
            publisher.urllib.request, 'urlopen', side_effect=[response, error])

    def test_owner_with_package_scope_can_confirm_missing_package(self):
        environment, http = self.check_owner_lookup()
        with environment, http as requests:
            self.assertTrue(publisher.package_is_missing())
            self.assertEqual(requests.call_count, 2)

    def test_wrong_owner_or_scope_cannot_confirm_missing_package(self):
        for owner, scopes in (('another-owner', 'write:packages'), ('H2OKing89', 'repo')):
            with self.subTest(owner=owner, scopes=scopes):
                environment, http = self.check_owner_lookup(owner, scopes)
                with environment, http as requests, self.assertRaisesRegex(ValueError, 'owner classic token'):
                    publisher.package_is_missing()
                self.assertEqual(requests.call_count, 1)

    def test_package_permission_failure_cannot_confirm_missing_package(self):
        environment, http = self.check_owner_lookup(status=403)
        with environment, http, self.assertRaises(urllib.error.HTTPError):
            publisher.package_is_missing()

    @patch.object(publisher, 'package_is_missing', return_value=True)
    @patch.object(publisher.subprocess, 'run', return_value=Mock(returncode=1, stderr='denied'))
    def test_missing_owner_package_allows_initial_publish(self, run, missing):
        self.assertIsNone(publisher.pull_existing(publisher.REPOSITORY + ':0.1.0'))
        missing.assert_called_once()

    @patch.object(publisher, 'package_is_missing', return_value=False)
    @patch.object(publisher.subprocess, 'run', return_value=Mock(returncode=1, stderr='denied'))
    def test_existing_private_package_denial_never_treated_as_missing(self, run, missing):
        with self.assertRaisesRegex(ValueError, 'No tag was overwritten'):
            publisher.pull_existing(publisher.REPOSITORY + ':0.1.0')

    @patch.object(publisher, 'package_is_missing')
    @patch.object(publisher.subprocess, 'run', return_value=Mock(returncode=1, stderr='denied'))
    def test_anonymous_denial_never_uses_owner_credentials(self, run, missing):
        with self.assertRaises(ValueError):
            publisher.pull_existing(publisher.REPOSITORY + ':0.1.0', env={'DOCKER_CONFIG': '/empty'})
        missing.assert_not_called()


if __name__ == '__main__':
    unittest.main()
