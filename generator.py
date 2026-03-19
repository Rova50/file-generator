#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""File/directory generator and ZIP builder."""

import os
import logging
import zipfile
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Content templates
# ---------------------------------------------------------------------------

def _vue_template(name: str) -> str:
    low = name.lower()
    return f'''<template>
    <div class="{low}">
        <h2>{name}</h2>
        <p>Contenu du composant {name}</p>
    </div>
</template>

<script>
export default {{
    name: '{name}',
    data() {{
        return {{ message: 'Bienvenue dans {name}' }}
    }},
    methods: {{}}
}}
</script>

<style scoped>
.{low} {{ padding: 20px; margin: 10px; border: 1px solid #e0e0e0; border-radius: 4px; }}
</style>'''


_CONTENT_TEMPLATES = {
    '.vue': lambda f: _vue_template(os.path.splitext(f)[0]),
    '.js': lambda f: (
        '''import Vue from 'vue'\nimport App from './App.vue'\n\nVue.config.productionTip = false\n\nnew Vue({ render: h => h(App) }).$mount('#app')'''
        if f == 'main.js'
        else f"// {f}\nexport default {{ name: '{os.path.splitext(f)[0]}' }}"
    ),
    '.css': lambda f: f"/* {f} */\n",
    '.html': lambda f: (
        f'<!DOCTYPE html>\n<html lang="fr">\n<head>\n    <meta charset="UTF-8">\n'
        f'    <title>{f}</title>\n</head>\n<body>\n    <h1>{f}</h1>\n</body>\n</html>'
    ),
    '.json': lambda f: f'{{\n    "name": "{f}",\n    "version": "1.0.0"\n}}',
}


# ---------------------------------------------------------------------------
# FileGenerator
# ---------------------------------------------------------------------------

class FileGenerator:
    def __init__(self, base_path):
        self.base_path = Path(base_path)

    def generate_content(self, filename: str):
        ext = os.path.splitext(filename)[1]
        fn = _CONTENT_TEMPLATES.get(ext)
        return fn(filename) if fn else None

    def generate_structure(self, structure: list, options: dict = None) -> dict:
        options = options or {}
        results = {
            'success': True,
            'directories': [],
            'files': [],
            'errors': [],
            'stats': {'dirs_created': 0, 'files_created': 0, 'total_size': 0},
        }

        for item in structure:
            full_path = self.base_path / item['path']
            try:
                if item['type'] == 'directory':
                    full_path.mkdir(parents=True, exist_ok=True)
                    results['directories'].append(str(full_path))
                    results['stats']['dirs_created'] += 1
                    logger.info(f"Dir: {full_path}")
                else:
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    if full_path.exists() and not options.get('overwrite', False):
                        results['errors'].append({'path': str(full_path), 'error': 'Fichier déjà existant'})
                        continue
                    content = self.generate_content(item['name']) if options.get('generate_content', True) else ''
                    full_path.write_text(content or f'// {item["name"]}\n', encoding='utf-8')
                    size = full_path.stat().st_size
                    results['files'].append({'path': str(full_path), 'size': size})
                    results['stats']['files_created'] += 1
                    results['stats']['total_size'] += size
                    logger.info(f"File: {full_path} ({size}b)")
            except Exception as e:
                results['errors'].append({'path': item['path'], 'error': str(e)})
                logger.error(f"Error on {item['path']}: {e}")

        results['success'] = len(results['errors']) == 0
        return results

    def create_zip(self, folder: Path) -> Path:
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_path = folder.parent / f"structure_{stamp}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in folder.rglob('*'):
                if f.is_file():
                    zf.write(f, f.relative_to(folder))
        return zip_path


# ---------------------------------------------------------------------------
# Preview helper
# ---------------------------------------------------------------------------

def generate_preview_text(structure: list) -> str:
    lines = ["📋 APERÇU DE LA STRUCTURE", "════════════════════════", ""]
    for item in structure:
        indent = "  " * item['level']
        icon = "📁" if item['type'] == 'directory' else "📄"
        suffix = "/" if item['type'] == 'directory' else ""
        lines.append(f"{indent}{icon} {item['name']}{suffix}")
    dirs = sum(1 for i in structure if i['type'] == 'directory')
    files = sum(1 for i in structure if i['type'] == 'file')
    lines.append(f"\nTotal: {dirs} dossiers, {files} fichiers")
    return "\n".join(lines)
