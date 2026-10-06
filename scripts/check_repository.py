#!/usr/bin/env python3
"""Offline syntax, evidence JSON and relative Markdown link checks for CI."""
import ast
import json
import re
import subprocess
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def unraid_template_issues(template):
    """Reject install defaults that break the adapter's deployment contract."""
    issues = []
    if template.tag != 'Container' or template.get('version') != '2':
        issues.append('expected Unraid Container version 2')
    if template.findtext('Repository') != 'ghcr.io/h2oking89/abs-audiobookdb:latest':
        issues.append('default image must use the project latest release channel')
    if template.findtext('Privileged') != 'false':
        issues.append('privileged mode must be disabled')
    required = {'--user=99:100', '--read-only', '--memory=256m', '--cap-drop=ALL',
                '--security-opt=no-new-privileges'}
    if not required.issubset(set((template.findtext('ExtraParams') or '').split())):
        issues.append('required runtime restrictions missing')
    configs = {item.get('Target'): item for item in template.findall('Config')}
    contact = configs.get('AUDIOBOOKDB_CONTACT')
    if contact is None or contact.get('Required') != 'true' or contact.get('Default') or (contact.text or '').strip():
        issues.append('operator must supply their own required contact')
    if any('KEY' in name or name.startswith('ABS_') for name in configs if name):
        issues.append('credentials and development ABS settings do not belong in the template')
    return issues


def markdown_link_targets(text):
    """Find inline and defined reference links outside fenced code blocks."""
    lines = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if (marker and marker[1][0] == fence[0]
                    and len(marker[1]) >= len(fence)
                    and not marker[2].strip()):
                fence = None
        elif marker and (marker[1][0] == '~' or '`' not in marker[2]):
            fence = marker[1]
        else:
            lines.append(line)
    text = ''.join(lines)
    references = {}

    def label_key(label):
        return ' '.join(label.split()).casefold()

    def reference(match):
        references.setdefault(label_key(match[1]), match[2])
        return ''

    text = re.sub(r'^ {0,3}\[([^\]]+)\]:[ \t]*(<[^>\n]*>|[^\s]+)[^\n]*$',
                  reference, text, flags=re.M)
    for match in re.finditer(r'\[([^\]]*)\](?:\(([^\s)]+)\)|\[([^\]]*)\])?', text):
        if match[2] is not None:
            yield match[2]
        else:
            target = references.get(label_key(match[3] or match[1]))
            if target is not None:
                yield target


def main():
    names = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
                           cwd=ROOT, capture_output=True, check=True).stdout.split(b'\0')
    paths = sorted({ROOT / name.decode() for name in names if name})
    issues = []
    links = 0
    for path in paths:
        if not path.is_file():
            continue
        if path.suffix == '.py':
            ast.parse(path.read_text(), filename=str(path.relative_to(ROOT)))
        elif path.suffix in ('.cjs', '.js'):
            subprocess.run(['node', '--check', str(path)], check=True, capture_output=True)
        elif path.suffix == '.sh':
            subprocess.run(['bash', '-n', str(path)], check=True, capture_output=True)
        elif path.suffix == '.json':
            json.loads(path.read_text())
        elif path.suffix in ('.xml', '.svg'):
            tree = ET.parse(path).getroot()
            if path.parent == ROOT / 'templates':
                issues.extend(str(path.relative_to(ROOT)) + ': ' + issue
                              for issue in unraid_template_issues(tree))
            elif path.name == 'ca_profile.xml':
                if tree.tag != 'CommunityApplications' or not (tree.findtext('Profile') or '').strip():
                    issues.append('ca_profile.xml: repository profile is required')
        elif path.suffix == '.md':
            # Anchors/external URLs aren't filesystem links. Fenced examples
            # may demonstrate placeholder links and are not navigation targets.
            for target in markdown_link_targets(path.read_text()):
                target = target.strip('<>')
                if re.match(r'[A-Za-z][A-Za-z0-9+.-]*:', target) or target.startswith('#'):
                    continue
                name = urllib.parse.unquote(target.split('#', 1)[0])
                if not name:
                    continue
                links += 1
                if not (path.parent / name).exists():
                    issues.append(str(path.relative_to(ROOT)) + ': missing link ' + name)
    if issues:
        raise SystemExit('\n'.join(issues))
    print(f'Repository checks passed: {len(paths)} files, {links} relative links; Python/JS/shell syntax, JSON/XML/SVG and Unraid defaults valid.')


if __name__ == '__main__':
    main()
