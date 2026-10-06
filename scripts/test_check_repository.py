"""Offline regression fixtures for repository Markdown link validation."""
import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import check_repository


class MarkdownLinkTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True,
                       capture_output=True)

    def check(self, text):
        (self.root / 'README.md').write_text(text)
        output = io.StringIO()
        with mock.patch.object(check_repository, 'ROOT', self.root):
            with contextlib.redirect_stdout(output):
                check_repository.main()
        return output.getvalue()

    def test_uri_schemes_and_fragments(self):
        targets = ['https://example.invalid', 'mailto:reader@example.invalid',
                   'urn:isbn:123', 'git+ssh://example.invalid', 'custom.v1-test:value',
                   'A:value', '#section', '<#section>']
        text = '\n'.join(f'[link]({target})' for target in targets)
        text += '\n[mail][contact]\n[contact]: mailto:reader@example.invalid\n'
        text += '[section][anchor]\n[anchor]: #section\n'
        self.assertIn('0 relative links', self.check(text))

    def test_invalid_schemes_remain_filesystem_targets(self):
        with self.assertRaises(SystemExit) as error:
            self.check('[one](1bad:value)\n[two](bad_scheme:value)\n')
        self.assertEqual(str(error.exception),
                         'README.md: missing link 1bad:value\n'
                         'README.md: missing link bad_scheme:value')

    def test_fences_ignore_inline_links_references_and_definitions(self):
        for fence in ('```', '~~~', '````', '~~~~'):
            with self.subTest(fence=fence):
                text = (f'  {fence}markdown\n[inline](missing.md)\n'
                        '[guide][install]\n[install]: missing.md\n'
                        f'  {fence}\n[guide][install]\n')
                self.assertIn('0 relative links', self.check(text))

    def test_fence_closing_requires_matching_character_and_length(self):
        for opening, invalid in [('````', '```'), ('~~~~', '~~~'),
                                 ('```', '~~~'), ('~~~', '```')]:
            with self.subTest(opening=opening, invalid=invalid):
                text = (f'{opening}\n{invalid}\n[hidden](missing.md)\n'
                        f'{opening}  \n[visible](outside.md)\n')
                with self.assertRaisesRegex(SystemExit, '^README.md: missing link outside.md$'):
                    self.check(text)
        self.assertIn('0 relative links', self.check('~~~\n[hidden](missing.md)\n'))

    def test_reference_forms_and_existing_local_link_validation(self):
        (self.root / 'install guide.md').touch()
        text = ('[inline](install%20guide.md#start)\n[guide][ INSTALL  GUIDE ]\n'
                '[Install Guide][]\n[install guide]\n[undefined][missing]\n'
                '[install guide]: <install%20guide.md#start> "Installation"\n')
        self.assertIn('4 relative links', self.check(text))

    def test_missing_inline_and_reference_targets_outside_fences(self):
        text = ('~~~\n[ignored](example.md)\n~~~\n[inline](inline.md#start)\n'
                '[guide][install]\n[install]: missing%20guide.md#start\n')
        with self.assertRaises(SystemExit) as error:
            self.check(text)
        self.assertEqual(str(error.exception),
                         'README.md: missing link inline.md\n'
                         'README.md: missing link missing guide.md')


if __name__ == '__main__':
    unittest.main()
