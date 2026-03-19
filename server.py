#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Flask server — routes only. Logic lives in parser.py and generator.py."""

import os
import logging
import shutil
from pathlib import Path
from datetime import datetime

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from tree_parser import StructureParser
from generator import FileGenerator, generate_preview_text

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

UPLOAD_FOLDER = 'uploads'
GENERATED_FOLDER = 'generated'

for _d in [UPLOAD_FOLDER, GENERATED_FOLDER]:
    os.makedirs(_d, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_content(content: str):
    """Shared parse + stats helper."""
    structure = StructureParser().parse(content)
    dirs = [i for i in structure if i['type'] == 'directory']
    files = [i for i in structure if i['type'] == 'file']
    return structure, {
        'total_items': len(structure),
        'directories': len(dirs),
        'files': len(files),
        'file_size': len(content),
    }


def _guard_generated(path_str: str) -> tuple[Path, str | None]:
    """Resolve path and verify it's under GENERATED_FOLDER. Returns (path, error)."""
    target = Path(path_str).resolve()
    root = Path(GENERATED_FOLDER).resolve()
    if not str(target).startswith(str(root)):
        return target, 'Chemin non autorisé'
    return target, None

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uploads': os.path.exists(UPLOAD_FOLDER),
        'generated': os.path.exists(GENERATED_FOLDER),
    })


@app.route('/api/parse', methods=['POST'])
def parse_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'error': 'Nom de fichier vide'}), 400
    if not f.filename.endswith('.txt'):
        return jsonify({'error': 'Le fichier doit être au format .txt'}), 400
    try:
        structure, stats = _parse_content(f.read().decode('utf-8'))
        return jsonify({'success': True, 'structure': structure, 'stats': stats})
    except Exception as e:
        logger.error(f"parse_file: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/parse-text', methods=['POST'])
def parse_text():
    data = request.get_json() or {}
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Contenu vide'}), 400
    try:
        structure, stats = _parse_content(content)
        return jsonify({'success': True, 'structure': structure, 'stats': stats})
    except Exception as e:
        logger.error(f"parse_text: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/preview', methods=['POST'])
def preview():
    data = request.get_json() or {}
    structure = data.get('structure')
    if not structure:
        return jsonify({'error': 'Structure non fournie'}), 400
    return jsonify({
        'success': True,
        'structure': structure,
        'preview': generate_preview_text(structure),
    })


@app.route('/api/validate', methods=['POST'])
def validate():
    data = request.get_json() or {}
    structure = data.get('structure')
    if structure is None:
        return jsonify({'error': 'Structure non fournie'}), 400

    warnings = []
    if not structure:
        return jsonify({'success': True, 'valid': False, 'warnings': ['Structure vide']})

    max_depth = max(i['level'] for i in structure)
    if max_depth > 10:
        warnings.append(f'Profondeur excessive : {max_depth} niveaux (max recommandé : 10)')

    paths = [i['path'] for i in structure]
    dupes = list({p for p in paths if paths.count(p) > 1})
    if dupes:
        warnings.append(f"Chemins dupliqués : {', '.join(dupes)}")

    no_ext = [i for i in structure if i['type'] == 'file' and not i.get('extension')]
    if no_ext:
        warnings.append(f"{len(no_ext)} fichier(s) sans extension")

    dirs = [i for i in structure if i['type'] == 'directory']
    files = [i for i in structure if i['type'] == 'file']
    return jsonify({
        'success': True,
        'valid': len(warnings) == 0,
        'warnings': warnings,
        'stats': {'total_items': len(structure), 'directories': len(dirs), 'files': len(files)},
    })


@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Données JSON invalides'}), 400

    structure = data.get('structure', [])
    target_path = data.get('targetPath', GENERATED_FOLDER)
    options = data.get('options', {})

    if target_path == GENERATED_FOLDER:
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        target_path = os.path.join(GENERATED_FOLDER, f'generation_{stamp}')

    try:
        gen = FileGenerator(target_path)
        results = gen.generate_structure(structure, options)
        results['targetPath'] = str(Path(target_path).resolve())

        if options.get('createZip') and results['success']:
            zip_path = gen.create_zip(Path(target_path))
            results['zipFile'] = str(zip_path)

        return jsonify(results)
    except Exception as e:
        logger.error(f"generate: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/create-zip', methods=['POST'])
def create_zip():
    data = request.get_json() or {}
    if 'targetPath' not in data:
        return jsonify({'error': 'Chemin cible non fourni'}), 400

    target, err = _guard_generated(data['targetPath'])
    if err:
        return jsonify({'error': err}), 403
    if not target.exists():
        return jsonify({'error': 'Dossier introuvable'}), 404

    try:
        zip_path = FileGenerator(target).create_zip(target)
        return jsonify({'success': True, 'zipFile': str(zip_path), 'zipFilename': zip_path.name})
    except Exception as e:
        logger.error(f"create_zip: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/delete-folder', methods=['POST'])
def delete_folder():
    data = request.get_json() or {}
    if 'targetPath' not in data:
        return jsonify({'error': 'Chemin cible non fourni'}), 400

    target, err = _guard_generated(data['targetPath'])
    if err:
        return jsonify({'error': err}), 403
    if target == Path(GENERATED_FOLDER).resolve():
        return jsonify({'error': 'Impossible de supprimer le dossier racine'}), 403
    if not target.exists():
        return jsonify({'success': True, 'message': 'Déjà supprimé'})

    try:
        shutil.rmtree(target)
        return jsonify({'success': True, 'message': f'Supprimé : {target.name}'})
    except Exception as e:
        logger.error(f"delete_folder: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<path:filename>')
def download(filename):
    safe = secure_filename(os.path.basename(filename))
    path = os.path.join(GENERATED_FOLDER, safe)
    if not os.path.exists(path):
        return jsonify({'error': 'Fichier non trouvé'}), 404
    return send_file(path, as_attachment=True)


@app.route('/api/clean', methods=['POST'])
def clean():
    older_than = (request.json or {}).get('olderThan', 24)
    now = datetime.now().timestamp()
    count = 0
    for item in Path(GENERATED_FOLDER).glob('*'):
        if item.is_file() and (now - item.stat().st_mtime) > older_than * 3600:
            item.unlink()
            count += 1
        elif item.is_dir():
            try:
                item.rmdir()
                count += 1
            except OSError:
                pass
    return jsonify({'success': True, 'cleaned': count})

# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_):
    return jsonify({'error': 'Route non trouvée'}), 404

@app.errorhandler(500)
def internal_error(_):
    return jsonify({'error': 'Erreur interne du serveur'}), 500

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print(f"🚀 http://localhost:5000  |  uploads={UPLOAD_FOLDER}  generated={GENERATED_FOLDER}")
    app.run(host='0.0.0.0', port=5000, debug=True)
