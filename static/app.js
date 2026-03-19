class FileStructureGenerator {
    constructor() {
        this.apiUrl = window.location.origin + '/api';
        this.treeFile = null;
        this.currentStructure = null;
        this.initElements();
        this.initEventListeners();
        this.loadHistory();
        window.generator = this;
    }

    initElements() {
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('treeFile');
        this.selectFileBtn = document.getElementById('selectFileBtn');
        this.removeFileBtn = document.getElementById('removeFileBtn');
        this.fileInfo = document.getElementById('fileInfo');
        this.fileName = document.querySelector('.file-name');
        this.filePreview = document.getElementById('filePreview');
        this.fileContent = document.getElementById('fileContent');

        this.folderPathInput = document.getElementById('folderPath');
        this.browseFolderBtn = document.getElementById('browseFolderBtn');
        this.folderInfo = document.getElementById('folderInfo');
        this.folderPathSpan = document.querySelector('.folder-path');
        this.removeFolderBtn = document.getElementById('removeFolderBtn');

        this.overwriteCheckbox = document.getElementById('overwrite');
        this.createContentCheckbox = document.getElementById('createContent');
        this.dryRunCheckbox = document.getElementById('dryRun');
        this.createZipCheckbox = document.getElementById('createZip');
        this.recursiveCheckbox = document.getElementById('recursive');
        this.preserveCommentsCheckbox = document.getElementById('preserveComments');

        this.generateBtn = document.getElementById('generateBtn');
        this.previewBtn = document.getElementById('previewBtn');
        this.validateBtn = document.getElementById('validateBtn');

        this.outputSection = document.getElementById('outputSection');
        this.output = document.getElementById('output');
        this.copyOutputBtn = document.getElementById('copyOutputBtn');
        this.clearOutputBtn = document.getElementById('clearOutputBtn');
        this.downloadZipBtn = document.getElementById('downloadZipBtn');

        this.historyList = document.getElementById('historyList');
        this.toast = document.getElementById('toast');

        this.pasteContent = document.getElementById('pasteContent');
        this.parseTextBtn = document.getElementById('parseTextBtn');

        this.folderActions = document.getElementById('folderActions');
        this.generatedPathDisplay = document.getElementById('generatedPathDisplay');
        this.copyPathBtn = document.getElementById('copyPathBtn');
        this.createZipBtn = document.getElementById('createZipBtn');
        this.autoDeleteAfterZip = document.getElementById('autoDeleteAfterZip');
        this.deleteFolderBtn = document.getElementById('deleteFolderBtn');

        this.lastGeneratedPath = null;
    }

    initEventListeners() {
        this.dropZone.addEventListener('click', () => this.fileInput.click());
        this.dropZone.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.dropZone.addEventListener('dragleave', () => this.handleDragLeave());
        this.dropZone.addEventListener('drop', (e) => this.handleDrop(e));

        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.removeFileBtn.addEventListener('click', () => this.removeFile());

        this.folderPathInput.addEventListener('input', (e) => this.handleFolderPath(e));
        this.browseFolderBtn.addEventListener('click', () => this.browseFolder());
        this.removeFolderBtn.addEventListener('click', () => this.removeFolder());

        if (this.parseTextBtn) {
            this.parseTextBtn.addEventListener('click', () => this.parseTextContent());
        }
        if (this.pasteContent) {
            this.pasteContent.addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    e.preventDefault();
                    this.parseTextContent();
                }
            });
        }

        if (this.copyPathBtn) {
            this.copyPathBtn.addEventListener('click', () => this.copyGeneratedPath());
        }
        if (this.createZipBtn) {
            this.createZipBtn.addEventListener('click', () => this.createZipOnDemand());
        }
        if (this.deleteFolderBtn) {
            this.deleteFolderBtn.addEventListener('click', () => this.deleteGeneratedFolder());
        }

        this.generateBtn.addEventListener('click', () => this.generate());
        this.previewBtn.addEventListener('click', () => this.preview());
        this.copyOutputBtn.addEventListener('click', () => this.copyOutput());
        this.clearOutputBtn.addEventListener('click', () => this.clearOutput());
        this.downloadZipBtn.addEventListener('click', () => this.downloadZip());

        ['change', 'input'].forEach(event => {
            this.folderPathInput.addEventListener(event, () => this.checkGenerateButton());
        });

        this.checkServerHealth();
    }

    async checkServerHealth() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            const data = await response.json();
            const statusEl = document.getElementById('serverStatus');
            if (statusEl) {
                statusEl.textContent = 'En ligne';
                statusEl.className = 'server-status online';
            }
            console.log('Serveur OK:', data);
        } catch (error) {
            console.error('Serveur indisponible:', error);
            this.showError('Le serveur n\'est pas accessible');
        }
    }

    handleDragOver(e) {
        e.preventDefault();
        this.dropZone.classList.add('dragover');
    }

    handleDragLeave() {
        this.dropZone.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        this.dropZone.classList.remove('dragover');

        const file = e.dataTransfer.files[0];
        if (file && file.name.endsWith('.txt')) {
            this.treeFile = file;
            this.displayFileInfo(file);
            this.uploadAndParseFile(file);
        } else {
            this.showError('Veuillez sélectionner un fichier .txt');
        }
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.treeFile = file;
            this.displayFileInfo(file);
            this.uploadAndParseFile(file);
        }
    }

    handleFolderPath(e) {
        this.folderPath = e.target.value;
        if (this.folderPath) {
            this.folderInfo.style.display = 'flex';
            this.folderPathSpan.textContent = this.folderPath;
        } else {
            this.folderInfo.style.display = 'none';
        }
        this.checkGenerateButton();
    }

    browseFolder() {
        this.folderPathInput.focus();
        this.showToast('Saisissez le chemin du dossier dans le champ ci-dessus', 'info');
    }

    removeFile() {
        this.treeFile = null;
        this.currentStructure = null;
        this.fileInput.value = '';
        this.fileInfo.style.display = 'none';
        this.filePreview.style.display = 'none';
        this.fileContent.textContent = '';
        this.checkGenerateButton();
    }

    removeFolder() {
        this.folderPath = '';
        this.folderPathInput.value = '';
        this.folderInfo.style.display = 'none';
        this.checkGenerateButton();
    }

    displayFileInfo(file) {
        this.fileInfo.style.display = 'flex';
        this.fileName.textContent = `${file.name} (${(file.size / 1024).toFixed(2)} KB)`;
    }

    async parseTextContent() {
        const text = this.pasteContent ? this.pasteContent.value.trim() : '';
        if (!text) {
            this.showToast('Collez d\'abord une arborescence dans le champ texte', 'error');
            return;
        }

        this.showLoading();
        try {
            const response = await fetch(`${this.apiUrl}/parse-text`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: text })
            });
            const data = await response.json();

            if (data.success) {
                this.currentStructure = data.structure;
                this.treeFile = null;
                this.fileInput.value = '';
                this.fileInfo.style.display = 'none';

                this.filePreview.style.display = 'block';
                this.fileContent.textContent = text;

                const statsEl = document.getElementById('previewStats');
                if (statsEl) {
                    statsEl.innerHTML = `<p>📊 ${data.stats.directories} dossiers, ${data.stats.files} fichiers trouvés</p>`;
                }

                this.checkGenerateButton();
                this.showToast(`Structure analysée : ${data.stats.directories} dossiers, ${data.stats.files} fichiers`, 'success');
            } else {
                this.showError(data.error || 'Erreur lors du parsing');
            }
        } catch (error) {
            this.showError('Erreur de connexion au serveur');
            console.error(error);
        } finally {
            this.hideLoading();
        }
    }

    async uploadAndParseFile(file) {
        this.showLoading();

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${this.apiUrl}/parse`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.currentStructure = data.structure;
                this.displayFilePreview(file, data);
                this.checkGenerateButton();
            } else {
                this.showError(data.error || 'Erreur lors du parsing');
            }
        } catch (error) {
            this.showError('Erreur de connexion au serveur');
            console.error(error);
        } finally {
            this.hideLoading();
        }
    }

    displayFilePreview(file, data) {
        const reader = new FileReader();
        reader.onload = (e) => {
            this.filePreview.style.display = 'block';
            this.fileContent.textContent = e.target.result;

            const statsEl = document.getElementById('previewStats');
            if (statsEl) {
                statsEl.innerHTML = `<p>📊 ${data.stats.directories} dossiers, ${data.stats.files} fichiers trouvés</p>`;
            }
        };
        reader.readAsText(file);
    }

    checkGenerateButton() {
        const enabled = !!(this.currentStructure && this.folderPath);
        this.generateBtn.disabled = !enabled;
        this.previewBtn.disabled = !enabled;
        if (this.validateBtn) this.validateBtn.disabled = !this.currentStructure;
    }

    validateStructure() {
        const issues = [];
        if (!this.currentStructure || this.currentStructure.length === 0) {
            issues.push('Structure vide');
            return issues;
        }

        // Check max depth
        const maxDepth = Math.max(...this.currentStructure.map(i => i.level));
        if (maxDepth > 10) {
            issues.push(`Profondeur excessive: ${maxDepth} niveaux (max recommandé: 10)`);
        }

        // Check for duplicate paths
        const paths = this.currentStructure.map(i => i.path);
        const duplicates = paths.filter((p, i) => paths.indexOf(p) !== i);
        if (duplicates.length > 0) {
            issues.push(`Chemins dupliqués: ${[...new Set(duplicates)].join(', ')}`);
        }

        // Check for files without extension
        const suspiciousFiles = this.currentStructure.filter(i => i.type === 'file' && !i.extension);
        if (suspiciousFiles.length > 0) {
            issues.push(`${suspiciousFiles.length} fichier(s) sans extension détecté(s)`);
        }

        return issues;
    }

    async preview() {
        await this.process('preview');
    }

    async generate() {
        await this.process('generate');
    }

    async process(mode) {
        this.showLoading();

        try {
            const options = {
                overwrite: this.overwriteCheckbox.checked,
                generate_content: this.createContentCheckbox.checked,
                dryRun: this.dryRunCheckbox.checked,
                createZip: this.createZipCheckbox ? this.createZipCheckbox.checked : false,
                recursive: this.recursiveCheckbox ? this.recursiveCheckbox.checked : true,
                preserveComments: this.preserveCommentsCheckbox ? this.preserveCommentsCheckbox.checked : false
            };

            const payload = {
                structure: this.currentStructure,
                targetPath: this.folderPath,
                options: options
            };

            const endpoint = mode === 'preview' ? 'preview' : 'generate';

            const response = await fetch(`${this.apiUrl}/${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (data.success || data.preview) {
                this.displayOutput(data, mode);
                if (mode === 'generate' && data.success) {
                    this.saveToHistory(data);
                    if (data.targetPath) {
                        this.lastGeneratedPath = data.targetPath;
                        this.showFolderActions(data.targetPath);
                    }
                }
            } else {
                this.showError(data.error || `Erreur lors de la ${mode === 'preview' ? 'prévisualisation' : 'génération'}`);
            }
        } catch (error) {
            this.showError('Erreur de connexion au serveur');
            console.error(error);
        } finally {
            this.hideLoading();
        }
    }

    displayOutput(data, mode) {
        let output = '';

        if (mode === 'preview') {
            output = data.preview || this.generatePreviewText();
        } else {
            output = this.generateSuccessMessage(data);

            if (data.zipFile) {
                this.downloadZipBtn.style.display = 'inline-block';
                this.downloadZipBtn.dataset.file = data.zipFile;
            }

            if (data.stats) {
                const statsSection = document.getElementById('outputStats');
                if (statsSection) {
                    document.getElementById('statDirs').textContent = data.stats.dirs_created || 0;
                    document.getElementById('statFiles').textContent = data.stats.files_created || 0;
                    document.getElementById('statSize').textContent = this.formatSize(data.stats.total_size || 0);
                    statsSection.style.display = 'block';
                }
            }
        }

        this.output.textContent = output;
        this.showOutput();
    }

    generatePreviewText() {
        const preserveComments = this.preserveCommentsCheckbox && this.preserveCommentsCheckbox.checked;
        let preview = '📋 APERÇU DE LA STRUCTURE\n';
        preview += '════════════════════════\n\n';

        this.currentStructure.forEach(item => {
            const indent = '  '.repeat(item.level);
            const comment = preserveComments && item.comment ? `  (${item.comment})` : '';
            if (item.type === 'directory') {
                preview += `${indent}📁 ${item.name}/${comment}\n`;
            } else {
                preview += `${indent}📄 ${item.name}${comment}\n`;
            }
        });

        const dirs = this.currentStructure.filter(i => i.type === 'directory');
        const files = this.currentStructure.filter(i => i.type === 'file');
        preview += `\nTotal: ${dirs.length} dossiers, ${files.length} fichiers`;
        return preview;
    }

    generateSuccessMessage(data) {
        const preserveComments = this.preserveCommentsCheckbox && this.preserveCommentsCheckbox.checked;
        let message = '✅ STRUCTURE GÉNÉRÉE AVEC SUCCÈS\n';
        message += '════════════════════════════════\n\n';
        message += `📁 Dossier de destination: ${this.folderPath}\n\n`;
        message += '📋 Structure créée:\n';

        this.currentStructure.forEach(item => {
            const indent = '  '.repeat(item.level);
            const comment = preserveComments && item.comment ? `  (${item.comment})` : '';
            if (item.type === 'directory') {
                message += `${indent}📁 ${item.path}/${comment}\n`;
            } else {
                message += `${indent}📄 ${item.path}${comment}\n`;
            }
        });

        message += `\n📊 Résumé:\n`;
        message += `  • ${data.stats.dirs_created} dossiers créés\n`;
        message += `  • ${data.stats.files_created} fichiers créés\n`;
        message += `  • Taille totale: ${this.formatSize(data.stats.total_size)}\n`;

        if (data.errors && data.errors.length > 0) {
            message += `\n⚠️ Erreurs (${data.errors.length}):\n`;
            data.errors.forEach(err => {
                message += `  • ${err.path}: ${err.error}\n`;
            });
        }

        return message;
    }

    formatSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showOutput() {
        this.outputSection.style.display = 'block';
        this.outputSection.scrollIntoView({ behavior: 'smooth' });
    }

    copyOutput() {
        navigator.clipboard.writeText(this.output.textContent)
            .then(() => this.showToast('Copié !', 'success'))
            .catch(() => this.showToast('Erreur de copie', 'error'));
    }

    clearOutput() {
        this.output.textContent = '';
        this.outputSection.style.display = 'none';
        this.downloadZipBtn.style.display = 'none';
        const statsSection = document.getElementById('outputStats');
        if (statsSection) statsSection.style.display = 'none';
    }

    async downloadZip() {
        const zipFile = this.downloadZipBtn.dataset.file;
        if (zipFile) {
            window.location.href = `${this.apiUrl}/download/${encodeURIComponent(zipFile)}`;
        }
    }

    showLoading() {
        this.generateBtn.innerHTML = '<span class="spinner"></span> Traitement...';
        this.generateBtn.disabled = true;
        this.previewBtn.disabled = true;
        if (this.validateBtn) this.validateBtn.disabled = true;

        const progressContainer = document.getElementById('progressContainer');
        if (progressContainer) {
            progressContainer.style.display = 'block';
            document.getElementById('progressBar').style.width = '60%';
            document.getElementById('progressMessage').textContent = 'Traitement en cours...';
        }
    }

    hideLoading() {
        this.generateBtn.innerHTML = '<span class="btn-icon">⚡</span> Générer la structure';
        const enabled = !!(this.currentStructure && this.folderPath);
        this.generateBtn.disabled = !enabled;
        this.previewBtn.disabled = !enabled;
        if (this.validateBtn) this.validateBtn.disabled = !this.currentStructure;

        const progressContainer = document.getElementById('progressContainer');
        if (progressContainer) {
            document.getElementById('progressBar').style.width = '100%';
            setTimeout(() => {
                progressContainer.style.display = 'none';
                document.getElementById('progressBar').style.width = '0%';
            }, 500);
        }
    }

    showError(message) {
        this.output.textContent = `❌ ${message}`;
        this.showOutput();
        this.showToast(message, 'error');
    }

    showToast(message, type = 'success') {
        if (!this.toast) return;
        this.toast.textContent = message;
        this.toast.className = `toast ${type} show`;
        clearTimeout(this._toastTimer);
        this._toastTimer = setTimeout(() => {
            this.toast.classList.remove('show');
        }, 3000);
    }

    showTemporaryMessage(message) {
        const originalText = this.copyOutputBtn.textContent;
        this.copyOutputBtn.textContent = message;
        setTimeout(() => {
            this.copyOutputBtn.textContent = originalText;
        }, 2000);
    }

    // Folder actions

    showFolderActions(path) {
        if (!this.folderActions) return;
        this.lastGeneratedPath = path;
        if (this.generatedPathDisplay) this.generatedPathDisplay.textContent = path;
        this.folderActions.style.display = 'block';
    }

    hideFolderActions() {
        if (this.folderActions) this.folderActions.style.display = 'none';
        this.lastGeneratedPath = null;
    }

    copyGeneratedPath() {
        if (!this.lastGeneratedPath) return;
        navigator.clipboard.writeText(this.lastGeneratedPath)
            .then(() => this.showToast('Chemin copié !', 'success'))
            .catch(() => this.showToast('Erreur de copie', 'error'));
    }

    async createZipOnDemand() {
        if (!this.lastGeneratedPath) return;
        this.createZipBtn.disabled = true;
        this.createZipBtn.textContent = '⏳ Création du ZIP...';
        try {
            const response = await fetch(`${this.apiUrl}/create-zip`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ targetPath: this.lastGeneratedPath })
            });
            const data = await response.json();
            if (data.success) {
                window.location.href = `${this.apiUrl}/download/${encodeURIComponent(data.zipFilename)}`;
                this.showToast('Téléchargement du ZIP lancé', 'success');
                if (this.autoDeleteAfterZip && this.autoDeleteAfterZip.checked) {
                    setTimeout(() => this.deleteGeneratedFolder(true), 1500);
                }
            } else {
                this.showToast(data.error || 'Erreur lors de la création du ZIP', 'error');
            }
        } catch (error) {
            this.showToast('Erreur de connexion au serveur', 'error');
        } finally {
            this.createZipBtn.disabled = false;
            this.createZipBtn.textContent = '📦 Télécharger ZIP';
        }
    }

    async deleteGeneratedFolder(silent = false) {
        if (!this.lastGeneratedPath) return;
        if (!silent && !confirm(`Supprimer le dossier généré ?\n${this.lastGeneratedPath}`)) return;
        try {
            const response = await fetch(`${this.apiUrl}/delete-folder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ targetPath: this.lastGeneratedPath })
            });
            const data = await response.json();
            if (data.success) {
                this.showToast(data.message || 'Dossier supprimé', 'success');
                this.hideFolderActions();
            } else {
                this.showToast(data.error || 'Erreur lors de la suppression', 'error');
            }
        } catch (error) {
            this.showToast('Erreur de connexion au serveur', 'error');
        }
    }

    // History

    loadHistory() {
        try {
            const raw = localStorage.getItem('generationHistory');
            const history = raw ? JSON.parse(raw) : [];
            this.renderHistory(history);
        } catch (e) {
            console.warn('Could not load history:', e);
        }
    }

    saveToHistory(data) {
        try {
            const raw = localStorage.getItem('generationHistory');
            const history = raw ? JSON.parse(raw) : [];
            history.unshift({
                timestamp: new Date().toISOString(),
                path: this.folderPath,
                stats: data.stats
            });
            const trimmed = history.slice(0, 20);
            localStorage.setItem('generationHistory', JSON.stringify(trimmed));
            this.renderHistory(trimmed);
            this.showToast('Structure générée et sauvegardée dans l\'historique', 'success');
        } catch (e) {
            console.warn('Could not save history:', e);
        }
    }

    renderHistory(history) {
        const emptyMsg = '<p style="color: #9ca3af; text-align: center; padding: 1rem;">Aucun historique</p>';

        if (!history || history.length === 0) {
            if (this.historyList) this.historyList.innerHTML = emptyMsg;
            const modal = document.getElementById('modalHistoryList');
            if (modal) modal.innerHTML = emptyMsg;
            return;
        }

        const html = history.map(entry => {
            const date = new Date(entry.timestamp).toLocaleString('fr-FR');
            const dirs = entry.stats ? entry.stats.dirs_created : '?';
            const files = entry.stats ? entry.stats.files_created : '?';
            return `<div class="history-item">
                <div class="history-item-header">
                    <span style="font-weight: 500; font-size: 0.9rem;">${entry.path || '?'}</span>
                    <span class="history-item-date">${date}</span>
                </div>
                <div class="history-item-stats">
                    <span>📁 ${dirs} dossiers</span>
                    <span>📄 ${files} fichiers</span>
                </div>
            </div>`;
        }).join('');

        if (this.historyList) this.historyList.innerHTML = html;
        const modal = document.getElementById('modalHistoryList');
        if (modal) modal.innerHTML = html;
    }
}

// Initialiser l'application
document.addEventListener('DOMContentLoaded', () => {
    window.generator = new FileStructureGenerator();
});
