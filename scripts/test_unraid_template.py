"""Regression checks for portable, restricted Unraid install defaults."""
import unittest
import xml.etree.ElementTree as ET

from check_repository import ROOT, unraid_template_issues


class UnraidTemplateTests(unittest.TestCase):
    def setUp(self):
        self.template = ET.parse(ROOT / 'templates/abs-audiobookdb.xml').getroot()

    def test_shipped_template(self):
        self.assertEqual(unraid_template_issues(self.template), [])

    def test_privileged_or_unrestricted_install_rejected(self):
        self.template.find('Privileged').text = 'true'
        self.template.find('ExtraParams').text = '--read-only'
        issues = unraid_template_issues(self.template)
        self.assertIn('privileged mode must be disabled', issues)
        self.assertIn('required runtime restrictions missing', issues)

    def test_wrong_repository_or_channel_rejected(self):
        for image in ('other/abs-audiobookdb:latest',
                      'ghcr.io/h2oking89/abs-audiobookdb',
                      'ghcr.io/h2oking89/abs-audiobookdb:main',
                      'ghcr.io/h2oking89/abs-audiobookdb:0.1.0'):
            with self.subTest(image=image):
                self.template.find('Repository').text = image
                self.assertIn('default image must use the project latest release channel',
                              unraid_template_issues(self.template))

    def test_bundled_operator_contact_or_secret_rejected(self):
        contact = self.template.find("Config[@Target='AUDIOBOOKDB_CONTACT']")
        contact.set('Default', 'operator@example.invalid')
        ET.SubElement(self.template, 'Config', {'Target': 'AUDIOBOOKDB_API_KEY'})
        issues = unraid_template_issues(self.template)
        self.assertIn('operator must supply their own required contact', issues)
        self.assertIn('credentials and development ABS settings do not belong in the template', issues)


if __name__ == '__main__':
    unittest.main()
