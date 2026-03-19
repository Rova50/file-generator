#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Serveur Flask pour la génération de structure de fichiers
"""

import os
import re
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import zipfile
import tempfile

# Configuration
app = Flask(__name__,
            static_folder='static',
            static_url_path='/static')
CORS(app)

# Configuration des dossiers
UPLOAD_FOLDER = 'uploads'
GENERATED_FOLDER = 'generated'
ALLOWED_EXTENSIONS = {'txt'}

# Créer les dossiers nécessaires
for folder in [UPLOAD_FOLDER, GENERATED_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

class StructureParser:
    """Parseur de structure d'arborescence"""
    
    def __init__(self):
        self.standard_dirs = ['src', 'assets', 'css', 'js', 'components', 
                             'node_modules', 'public', 'views', 'router', 
                             'store', 'utils', 'helpers', 'mixins']
    
    def clean_name(self, name):
        """Nettoie le nom d'un fichier/dossier"""
        # Enlever les caractères d'arborescence
        name = re.sub(r'^[│├└─\s]+', '', name)
        # Enlever les commentaires # style
        name = re.sub(r'\s*#.*$', '', name)
        # Enlever les commentaires entre parenthèses
        name = re.sub(r'\s*\([^)]*\)\s*$', '', name)
        # Enlever les espaces
        return name.strip()

    def extract_comment(self, line):
        """Extrait le commentaire d'une ligne (# style ou parenthèses), s'il existe"""
        # Priorité au commentaire # style
        hash_match = re.search(r'#\s*(.+)$', line)
        if hash_match:
            return hash_match.group(1).strip()
        # Fallback sur les parenthèses
        paren_match = re.search(r'\(([^)]*)\)', line)
        return paren_match.group(1).strip() if paren_match else None
    
    def is_directory(self, name, line):
        """Détermine si un élément est un dossier"""
        # Si le nom se termine par /
        if name.endswith('/'):
            return True
        
        # Dossiers standards
        if name in self.standard_dirs:
            return True
        
        # Si la ligne contient des indicateurs de dossier
        if re.search(r'[│├└]\s*[a-zA-Z]+\/$', line):
            return True
        
        # Si le nom n'a pas d'extension → traiter comme dossier (comportement par défaut)
        if '.' not in name:
            return True

        return False
    
    def parse(self, content):
        """Parse le contenu et retourne la structure"""
        lines = content.split('\n')
        structure = []
        folder_stack = []
        last_level = -1
        
        for i, line in enumerate(lines):
            line = line.rstrip()
            if not line or line.isspace():
                continue
            
            # Compter le niveau d'indentation
            indent_match = re.match(r'^[│├└─\s]*', line)
            indent_chars = indent_match.group(0) if indent_match else ''
            level = indent_chars.count('│')
            
            # Extraire le commentaire avant nettoyage
            comment = self.extract_comment(line)

            # Nettoyer le nom
            name = self.clean_name(line)
            if not name:
                continue

            # Déterminer si c'est un dossier
            is_dir = self.is_directory(name, line)
            
            # Nettoyer le nom du dossier
            if is_dir:
                name = name.rstrip('/')
            
            # Ajuster la pile des dossiers
            if level > last_level:
                # On descend d'un niveau
                folder_stack = folder_stack[:level]
            elif level < last_level:
                # On remonte
                folder_stack = folder_stack[:level]
            
            # Construire le chemin complet
            if is_dir:
                # C'est un dossier
                folder_stack = folder_stack[:level]
                folder_stack.append(name)
                path = '/'.join(folder_stack)
                structure.append({
                    'type': 'directory',
                    'path': path,
                    'name': name,
                    'level': level,
                    'comment': comment
                })
            else:
                # C'est un fichier
                base_path = '/'.join(folder_stack[:level]) if folder_stack else ''
                path = f"{base_path}/{name}" if base_path else name
                ext = os.path.splitext(name)[1]
                structure.append({
                    'type': 'file',
                    'path': path,
                    'name': name,
                    'extension': ext,
                    'level': level,
                    'comment': comment
                })
            
            last_level = level
        
        return structure

class FileGenerator:
    """Générateur de fichiers"""
    
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.parser = StructureParser()
    
    def generate_content(self, filename):
        """Génère le contenu d'un fichier selon son type"""
        ext = os.path.splitext(filename)[1]
        
        if ext == '.vue':
            component_name = os.path.splitext(filename)[0]
            return f'''<template>
    <div class="{component_name.lower()}">
        <h2>{component_name}</h2>
        <p>Contenu du composant {component_name}</p>
    </div>
</template>

<script>
export default {{
    name: '{component_name}',
    data() {{
        return {{
            message: 'Bienvenue dans {component_name}'
        }}
    }},
    methods: {{
        // Vos méthodes ici
    }}
}}
</script>

<style scoped>
.{component_name.lower()} {{
    padding: 20px;
    margin: 10px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
}}
</style>'''
        
        elif ext == '.js':
            if filename == 'main.js':
                return '''import Vue from 'vue'
import App from './App.vue'

Vue.config.productionTip = false

new Vue({
    render: h => h(App),
}).$mount('#app')'''
            else:
                module_name = os.path.splitext(filename)[0]
                return f'''// Fichier JavaScript: {filename}
export default {{
    name: '{module_name}',
    // Configuration du module
}}'''
        
        elif ext == '.css':
            return f'''/* Fichier CSS: {filename} */
/* Copiez vos fichiers CSS ici */
/* @import 'chemin/vers/styles.css'; */
'''
        
        elif ext == '.html':
            return f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{filename}</title>
</head>
<body>
    <h1>{filename}</h1>
</body>
</html>'''
        
        elif ext == '.json':
            return f'''{{
    "name": "{filename}",
    "version": "1.0.0",
    "description": "Fichier généré automatiquement"
}}'''
        
        else:
            return None
    
    def generate_structure(self, structure, options=None):
        """Génère la structure complète"""
        if options is None:
            options = {}
        
        results = {
            'success': True,
            'directories': [],
            'files': [],
            'errors': [],
            'stats': {
                'dirs_created': 0,
                'files_created': 0,
                'total_size': 0
            }
        }
        
        for item in structure:
            full_path = self.base_path / item['path']
            
            try:
                if item['type'] == 'directory':
                    # Créer le dossier
                    if not full_path.exists() or options.get('overwrite', False):
                        full_path.mkdir(parents=True, exist_ok=True)
                        results['directories'].append(str(full_path))
                        results['stats']['dirs_created'] += 1
                        logger.info(f"Dossier créé: {full_path}")
                
                else:  # Fichier
                    # Créer le dossier parent si nécessaire
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Vérifier si le fichier existe
                    if full_path.exists() and not options.get('overwrite', False):
                        results['errors'].append({
                            'path': str(full_path),
                            'error': 'Le fichier existe déjà'
                        })
                        continue
                    
                    # Générer le contenu
                    if options.get('generate_content', True):
                        content = self.generate_content(item['name'])
                    else:
                        content = ''
                    
                    # Écrire le fichier
                    with open(full_path, 'w', encoding='utf-8') as f:
                        if content:
                            f.write(content)
                        else:
                            f.write(f'// Fichier: {item["name"]}\n')
                    
                    # Calculer la taille
                    size = full_path.stat().st_size
                    results['stats']['total_size'] += size
                    
                    results['files'].append({
                        'path': str(full_path),
                        'size': size,
                        'content_generated': bool(content)
                    })
                    results['stats']['files_created'] += 1
                    
                    logger.info(f"Fichier créé: {full_path} ({size} bytes)")
            
            except Exception as e:
                error_msg = f"Erreur lors de la création de {item['path']}: {str(e)}"
                results['errors'].append({
                    'path': item['path'],
                    'error': str(e)
                })
                logger.error(error_msg)
        
        results['success'] = len(results['errors']) == 0
        return results
    
    def create_zip_archive(self, structure):
        """Crée une archive ZIP de la structure générée"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"structure_{timestamp}.zip"
        zip_path = self.base_path / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item in structure:
                file_path = self.base_path / item['path']
                if file_path.exists():
                    arcname = str(file_path.relative_to(self.base_path))
                    zipf.write(file_path, arcname)
        
        return zip_path

# Routes API

@app.route('/')
def index():
    """Page d'accueil"""
    return app.send_static_file('index.html')

@app.route('/api/health', methods=['GET'])
def health():
    """Vérification de la santé du serveur"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uploads': os.path.exists(UPLOAD_FOLDER),
        'generated': os.path.exists(GENERATED_FOLDER)
    })

@app.route('/api/parse', methods=['POST'])
def parse_file():
    """Parse un fichier d'arborescence"""
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400
    
    if not file.filename.endswith('.txt'):
        return jsonify({'error': 'Le fichier doit être au format .txt'}), 400
    
    try:
        # Lire le contenu
        content = file.read().decode('utf-8')
        
        # Parser la structure
        parser = StructureParser()
        structure = parser.parse(content)
        
        # Statistiques
        dirs = [item for item in structure if item['type'] == 'directory']
        files = [item for item in structure if item['type'] == 'file']
        
        return jsonify({
            'success': True,
            'structure': structure,
            'stats': {
                'total_items': len(structure),
                'directories': len(dirs),
                'files': len(files),
                'file_size': len(content)
            }
        })
    
    except Exception as e:
        logger.error(f"Erreur lors du parsing: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate():
    """Génère la structure de fichiers"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données JSON invalides'}), 400
        
        structure = data.get('structure', [])
        target_path = data.get('targetPath', GENERATED_FOLDER)
        options = data.get('options', {})
        
        # Sécuriser le chemin cible
        if target_path == GENERATED_FOLDER:
            # Créer un sous-dossier avec timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            target_path = os.path.join(GENERATED_FOLDER, f"generation_{timestamp}")
        
        # Créer le générateur
        generator = FileGenerator(target_path)
        
        # Générer la structure
        results = generator.generate_structure(structure, options)
        
        # Créer une archive ZIP si demandé
        zip_path = None
        if options.get('createZip', False) and results['success']:
            zip_path = generator.create_zip_archive(structure)
            results['zipFile'] = str(zip_path)

        # Toujours retourner le chemin généré pour actions post-génération
        results['targetPath'] = str(Path(target_path).resolve())

        return jsonify(results)
    
    except Exception as e:
        logger.error(f"Erreur lors de la génération: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/preview', methods=['POST'])
def preview():
    """Prévisualise la structure sans créer les fichiers"""
    try:
        data = request.get_json()
        
        if not data or 'structure' not in data:
            return jsonify({'error': 'Structure non fournie'}), 400
        
        structure = data['structure']
        
        # Retourner la structure pour prévisualisation
        return jsonify({
            'success': True,
            'structure': structure,
            'preview': generate_preview_text(structure)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/parse-text', methods=['POST'])
def parse_text():
    """Parse du texte collé directement"""
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Contenu non fourni'}), 400

        content = data['content'].strip()
        if not content:
            return jsonify({'error': 'Le contenu est vide'}), 400

        parser = StructureParser()
        structure = parser.parse(content)

        dirs = [item for item in structure if item['type'] == 'directory']
        files = [item for item in structure if item['type'] == 'file']

        return jsonify({
            'success': True,
            'structure': structure,
            'stats': {
                'total_items': len(structure),
                'directories': len(dirs),
                'files': len(files),
                'file_size': len(content)
            }
        })

    except Exception as e:
        logger.error(f"Erreur lors du parsing du texte: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/create-zip', methods=['POST'])
def create_zip():
    """Crée un ZIP d'un dossier généré existant"""
    try:
        data = request.get_json()
        if not data or 'targetPath' not in data:
            return jsonify({'error': 'Chemin cible non fourni'}), 400

        target_path = Path(data['targetPath']).resolve()
        generated_root = Path(GENERATED_FOLDER).resolve()

        # Sécurité : le chemin doit être sous generated/
        if not str(target_path).startswith(str(generated_root)):
            return jsonify({'error': 'Chemin non autorisé'}), 403

        if not target_path.exists():
            return jsonify({'error': 'Dossier introuvable'}), 404

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"structure_{timestamp}.zip"
        zip_path = generated_root / zip_filename

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in target_path.rglob('*'):
                if file.is_file():
                    zipf.write(file, file.relative_to(target_path))

        return jsonify({
            'success': True,
            'zipFile': str(zip_path),
            'zipFilename': zip_filename
        })

    except Exception as e:
        logger.error(f"Erreur création ZIP: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/delete-folder', methods=['POST'])
def delete_folder():
    """Supprime un dossier généré"""
    try:
        data = request.get_json()
        if not data or 'targetPath' not in data:
            return jsonify({'error': 'Chemin cible non fourni'}), 400

        target_path = Path(data['targetPath']).resolve()
        generated_root = Path(GENERATED_FOLDER).resolve()

        # Sécurité : refuser si hors de generated/ ou si c'est la racine elle-même
        if not str(target_path).startswith(str(generated_root)):
            return jsonify({'error': 'Chemin non autorisé'}), 403
        if target_path == generated_root:
            return jsonify({'error': 'Impossible de supprimer le dossier racine'}), 403

        if not target_path.exists():
            return jsonify({'success': True, 'message': 'Dossier déjà supprimé'})

        shutil.rmtree(target_path)
        return jsonify({'success': True, 'message': f'Dossier supprimé : {target_path.name}'})

    except Exception as e:
        logger.error(f"Erreur suppression dossier: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/validate', methods=['POST'])
def validate():
    """Valide une structure sans créer de fichiers"""
    try:
        data = request.get_json()
        if not data or 'structure' not in data:
            return jsonify({'error': 'Structure non fournie'}), 400

        structure = data['structure']
        warnings = []

        if not structure:
            warnings.append('Structure vide')
            return jsonify({'success': True, 'valid': False, 'warnings': warnings})

        # Vérifier la profondeur max
        max_depth = max((item['level'] for item in structure), default=0)
        if max_depth > 10:
            warnings.append(f'Profondeur excessive: {max_depth} niveaux (max recommandé: 10)')

        # Vérifier les chemins dupliqués
        paths = [item['path'] for item in structure]
        duplicates = list({p for p in paths if paths.count(p) > 1})
        if duplicates:
            warnings.append(f"Chemins dupliqués: {', '.join(duplicates)}")

        # Fichiers sans extension
        no_ext = [i for i in structure if i['type'] == 'file' and not i.get('extension')]
        if no_ext:
            warnings.append(f"{len(no_ext)} fichier(s) sans extension détecté(s)")

        dirs = [i for i in structure if i['type'] == 'directory']
        files = [i for i in structure if i['type'] == 'file']

        return jsonify({
            'success': True,
            'valid': len(warnings) == 0,
            'warnings': warnings,
            'stats': {
                'total_items': len(structure),
                'directories': len(dirs),
                'files': len(files)
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<path:filename>', methods=['GET'])
def download(filename):
    """Télécharge un fichier généré"""
    try:
        # Sécuriser le nom du fichier
        safe_filename = secure_filename(os.path.basename(filename))
        file_path = os.path.join(GENERATED_FOLDER, safe_filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé'}), 404
        
        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clean', methods=['POST'])
def clean():
    """Nettoie les fichiers générés"""
    try:
        # Options de nettoyage
        older_than = request.json.get('olderThan', 24)  # Heures
        
        # Parcourir les fichiers générés
        count = 0
        for item in Path(GENERATED_FOLDER).glob('*'):
            if item.is_file():
                # Vérifier l'âge du fichier
                file_age = datetime.now().timestamp() - item.stat().st_mtime
                if file_age > older_than * 3600:  # Convertir en secondes
                    item.unlink()
                    count += 1
            elif item.is_dir():
                # Supprimer les dossiers vides
                try:
                    item.rmdir()
                    count += 1
                except OSError:
                    pass  # Dossier non vide
        
        return jsonify({
            'success': True,
            'cleaned': count,
            'message': f'{count} éléments nettoyés'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_preview_text(structure):
    """Génère un texte de prévisualisation"""
    preview = "📋 APERÇU DE LA STRUCTURE\n"
    preview += "════════════════════════\n\n"
    
    for item in structure:
        indent = "  " * item['level']
        if item['type'] == 'directory':
            preview += f"{indent}📁 {item['name']}/\n"
        else:
            preview += f"{indent}📄 {item['name']}\n"
    
    dirs = [i for i in structure if i['type'] == 'directory']
    files = [i for i in structure if i['type'] == 'file']
    
    preview += f"\nTotal: {len(dirs)} dossiers, {len(files)} fichiers"
    return preview

# Route pour les erreurs 404
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Route non trouvée'}), 404

# Route pour les erreurs 500
@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erreur interne du serveur'}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Serveur de génération de structure")
    print("=" * 50)
    print(f"📁 Dossier uploads: {UPLOAD_FOLDER}")
    print(f"📁 Dossier generated: {GENERATED_FOLDER}")
    print(f"🌐 http://localhost:5000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)