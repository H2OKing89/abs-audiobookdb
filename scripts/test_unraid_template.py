"""Regression checks for portable, restricted Unraid install defaults."""
import unittest
import xml.etree.ElementTree as ET

from check_repository import ROOT, unraid_template_issues


class UnraidTemplateTests(unittest.TestCase):
    def setUp(self):
        self.template = ET.parse(ROOT / 'templates/abs-audiobookdb.xml').getroot()
        self.version = (ROOT / 'internal/buildinfo/VERSION').read_text().strip()

    def test_shipped_template(self):
        self.assertEqual(unraid_template_issues(self.template, self.version), [])

    def test_privileged_or_unrestricted_install_rejected(self):
        self.template.find('Privileged').text = 'true'
        self.template.find('ExtraParams').text = '--read-only'
        issues = unraid_template_issues(self.template, self.version)
        self.assertIn('privileged mode must be disabled', issues)
        self.assertIn('required runtime restrictions missing', issues)

    def test_unpinned_image_rejected(self):
        self.template.find('Repository').text = 'ghcr.io/h2oking89/abs-audiobookdb:latest'
        self.assertIn('image must pin the current source version',
                      unraid_template_issues(self.template, self.version))

    def test_bundled_operator_contact_or_secret_rejected(self):
        contact = self.template.find("Config[@Target='AUDIOBOOKDB_CONTACT']")
        contact.set('Default', 'operator@example.invalid')
        ET.SubElement(self.template, 'Config', {'Target': 'AUDIOBOOKDB_API_KEY'})
        issues = unraid_template_issues(self.template, self.version)
        self.assertIn('operator must supply their own required contact', issues)
        self.assertIn('credentials and development ABS settings do not belong in the template', issues)


if __name__ == '__main__':
    unittest.main()
