#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ASCII tree parser — converts indented tree text into a list of path items."""

import os
import re


class StructureParser:
    STANDARD_DIRS = {
        'src', 'assets', 'css', 'js', 'components', 'node_modules',
        'public', 'views', 'router', 'store', 'utils', 'helpers', 'mixins',
    }

    def clean_name(self, name: str) -> str:
        name = re.sub(r'^[│├└─\s]+', '', name)
        name = re.sub(r'\s*#.*$', '', name)
        name = re.sub(r'\s*\([^)]*\)\s*$', '', name)
        return name.strip()

    def extract_comment(self, line: str):
        m = re.search(r'#\s*(.+)$', line)
        if m:
            return m.group(1).strip()
        m = re.search(r'\(([^)]*)\)', line)
        return m.group(1).strip() if m else None

    def is_directory(self, name: str, line: str) -> bool:
        if name.endswith('/'):
            return True
        if name in self.STANDARD_DIRS:
            return True
        if re.search(r'[│├└]\s*[a-zA-Z]+\/$', line):
            return True
        return '.' not in name

    def _level(self, line: str) -> int:
        """Compute nesting depth. Replace every tree-drawing char with a space,
        then count leading spaces. Standard tree output uses 4-char groups
        (e.g. '│   ' or '├── '), so divide by 4."""
        flat = re.sub(r'[│├└─]', ' ', line)
        spaces = len(flat) - len(flat.lstrip(' '))
        return spaces // 4

    def parse(self, content: str) -> list:
        structure = []
        folder_stack: list[str] = []

        for line in content.split('\n'):
            line = line.rstrip()
            if not line or line.isspace():
                continue

            level = self._level(line)
            comment = self.extract_comment(line)
            name = self.clean_name(line)
            if not name:
                continue

            is_dir = self.is_directory(name, line)
            if is_dir:
                name = name.rstrip('/')

            folder_stack = folder_stack[:level]

            if is_dir:
                folder_stack.append(name)
                structure.append({
                    'type': 'directory',
                    'path': '/'.join(folder_stack),
                    'name': name,
                    'level': level,
                    'comment': comment,
                })
            else:
                base = '/'.join(folder_stack) if folder_stack else ''
                path = f"{base}/{name}" if base else name
                structure.append({
                    'type': 'file',
                    'path': path,
                    'name': name,
                    'extension': os.path.splitext(name)[1],
                    'level': level,
                    'comment': comment,
                })

        return structure
