#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File structure generator — CLI companion.

Parses an ASCII-tree .txt file and scaffolds the structure on disk.
Reuses tree_parser.py and generator.py from the same directory.

Usage
-----
  python generate.py tree.txt ./my-project
  python generate.py tree.txt ./my-project --dry-run
  python generate.py tree.txt ./my-project --overwrite --no-content
  cat tree.txt | python generate.py - ./my-project
"""

import argparse
import sys
from pathlib import Path

# Allow running from any directory
sys.path.insert(0, str(Path(__file__).parent))

from tree_parser import StructureParser
from generator import FileGenerator

# ---------------------------------------------------------------------------
# ANSI colours (disabled on Windows if not supported)
# ---------------------------------------------------------------------------

def _supports_color():
    import os
    if sys.platform == 'win32':
        try:
            import ctypes
            kernel = ctypes.windll.kernel32
            kernel.SetConsoleMode(kernel.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

_COLOR = _supports_color()

def _c(code, text):
    return f"\033[{code}m{text}\033[0m" if _COLOR else text

def _ok(s):     return _c('32', '✓') + ' ' + s
def _warn(s):   return _c('33', '⚠') + ' ' + s
def _err(s):    return _c('31', '✗') + ' ' + s
def _bold(s):   return _c('1',  s)
def _dim(s):    return _c('2',  s)
def _blue(s):   return _c('34', s)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_size(b: int) -> str:
    for unit in ('B', 'KB', 'MB'):
        if b < 1024:
            return f'{b:.1f} {unit}'
        b //= 1024
    return f'{b:.1f} GB'


def _print_tree(structure: list, dry_run: bool = False):
    tag = _dim('[dry-run] ') if dry_run else ''
    for item in structure:
        indent = '  ' * item['level']
        if item['type'] == 'directory':
            line = f"{indent}{tag}{_blue('📁 ' + item['name'] + '/')}"
        else:
            line = f"{indent}{tag}📄 {item['name']}"
        if item.get('comment'):
            line += _dim(f"  # {item['comment']}")
        print('  ' + line)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog='generate.py',
        description='Scaffold a file/folder structure from an ASCII-tree .txt file.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python generate.py tree.txt ./my-project
  python generate.py tree.txt ./my-project --dry-run
  python generate.py tree.txt ./my-project --overwrite --no-content
  cat tree.txt | python generate.py - ./my-project
        """
    )
    parser.add_argument('tree_file',
                        help="Path to the .txt tree file, or '-' to read from stdin")
    parser.add_argument('target',
                        help='Target directory (created if it does not exist)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview what would be created without writing anything')
    parser.add_argument('--overwrite', action='store_true',
                        help='Overwrite existing files')
    parser.add_argument('--no-content', action='store_true',
                        help='Create empty files instead of using content templates')
    args = parser.parse_args()

    # --- Read source ----------------------------------------------------------
    if args.tree_file == '-':
        content = sys.stdin.read()
        source_name = '<stdin>'
    else:
        src = Path(args.tree_file)
        if not src.exists():
            print(_err(f'File not found: {src}'), file=sys.stderr)
            sys.exit(1)
        content = src.read_text(encoding='utf-8')
        source_name = str(src)

    # --- Parse ----------------------------------------------------------------
    structure = StructureParser().parse(content)
    if not structure:
        print(_err('No items parsed. Check the tree file format.'), file=sys.stderr)
        sys.exit(1)

    dirs  = [i for i in structure if i['type'] == 'directory']
    files = [i for i in structure if i['type'] == 'file']
    target = Path(args.target)

    # --- Summary header -------------------------------------------------------
    print()
    print(f'  {_bold("Source :")} {source_name}')
    print(f'  {_bold("Target :")} {target.resolve()}')
    print(f'  {_bold("Items  :")} {len(dirs)} dirs, {len(files)} files')
    if args.dry_run:
        print(f'  {_bold("Mode   :")} {_c("33", "DRY RUN — nothing will be written")}')
    print()

    _print_tree(structure, dry_run=args.dry_run)
    print()

    # --- Dry run stops here ---------------------------------------------------
    if args.dry_run:
        print(_ok(f'Dry run complete. {len(structure)} items would be created.'))
        print()
        return

    # --- Generate -------------------------------------------------------------
    target.mkdir(parents=True, exist_ok=True)
    results = FileGenerator(target).generate_structure(structure, {
        'overwrite': args.overwrite,
        'generate_content': not args.no_content,
    })

    for err in results['errors']:
        print(_warn(f"{err['path']}: {err['error']}"))

    s = results['stats']
    outcome = _ok if results['success'] else _warn
    print(outcome(
        f"Done — {s['dirs_created']} dirs, {s['files_created']} files"
        f"  ({_format_size(s['total_size'])})"
    ))
    print(f"  {_dim('→ ' + str(target.resolve()))}")
    print()


if __name__ == '__main__':
    main()
