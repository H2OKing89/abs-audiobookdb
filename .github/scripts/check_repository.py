#!/usr/bin/env python3
"""Offline syntax, evidence JSON and relative Markdown link checks for CI."""
import ast
import json
import re
import subprocess
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


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
        elif path.suffix == '.json':
            json.loads(path.read_text())
        elif path.suffix == '.md':
            # Anchors/external URLs aren't filesystem links. Fenced examples
            # may demonstrate placeholder links and are not navigation targets.
            text = re.sub(r'```.*?```', '', path.read_text(), flags=re.S)
            for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', text):
                target = target.strip('<>')
                if re.match(r'\w+://', target) or target.startswith('#'):
                    continue
                name = urllib.parse.unquote(target.split('#', 1)[0])
                if not name:
                    continue
                links += 1
                if not (path.parent / name).exists():
                    issues.append(str(path.relative_to(ROOT)) + ': missing link ' + name)
    if issues:
        raise SystemExit('\n'.join(issues))
    print(f'Repository checks passed: {len(paths)} files, {links} relative links; Python/JS syntax and JSON valid.')


if __name__ == '__main__':
    main()
