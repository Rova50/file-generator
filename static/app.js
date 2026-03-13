class FileStructureGenerator {
    constructor() {
        this.apiUrl = window.location.origin + '/api';
        this.treeFile = null;
        this.currentStructure = null;
        this.initElements();
        this.initEventListeners();
    }

    initElements() {
        // Éléments DOM (les mêmes que précédemment)
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
        
        this.generateBtn = document.getElementById('generateBtn');
        this.previewBtn = document.getElementById('previewBtn');
        
        this.outputSection = document.getElementById('outputSection');
        this.output = document.getElementById('output');
        this.copyOutputBtn = document.getElementById('copyOutputBtn');
        this.clearOutputBtn = document.getElementById('clearOutputBtn');
        this.downloadZipBtn = document.getElementById('downloadZipBtn');
    }

    initEventListeners() {
        // Gestion du fichier
        this.dropZone.addEventListener('click', () => this.fileInput.click());
        this.dropZone.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.dropZone.addEventListener('dragleave', () => this.handleDragLeave());
        this.dropZone.addEventListener('drop', (e) => this.handleDrop(e));
        
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.removeFileBtn.addEventListener('click', () => this.removeFile());
        
        // Gestion du dossier
        this.folderPathInput.addEventListener('input', (e) => this.handleFolderPath(e));
        this.browseFolderBtn.addEventListener('click', () => this.browseFolder());
        this.removeFolderBtn.addEventListener('click', () => this.removeFolder());
        
        // Actions
        this.generateBtn.addEventListener('click', () => this.generate());
        this.previewBtn.addEventListener('click', () => this.preview());
        this.copyOutputBtn.addEventListener('click', () => this.copyOutput());
        this.clearOutputBtn.addEventListener('click', () => this.clearOutput());
        this.downloadZipBtn.addEventListener('click', () => this.downloadZip());
        
        // Vérification des conditions
        ['change', 'input'].forEach(event => {
            this.folderPathInput.addEventListener(event, () => this.checkGenerateButton());
        });

        // Vérifier la santé du serveur
        this.checkServerHealth();
    }

    async checkServerHealth() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            const data = await response.json();
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
        // Note: Dans une vraie application, ceci serait géré par le serveur
        // Pour cette démo, on utilise un prompt
        const path = prompt('Entrez le chemin du dossier :', './generated');
        if (path) {
            this.folderPath = path;
            this.folderPathInput.value = path;
            this.folderInfo.style.display = 'flex';
            this.folderPathSpan.textContent = path;
            this.checkGenerateButton();
        }
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
            
            // Ajouter les stats
            const stats = document.createElement('div');
            stats.className = 'file-stats';
            stats.innerHTML = `
                <p>📊 ${data.stats.directories} dossiers, ${data.stats.files} fichiers trouvés</p>
            `;
            this.filePreview.appendChild(stats);
        };
        reader.readAsText(file);
    }

    checkGenerateButton() {
        const enabled = this.currentStructure && this.folderPath;
        this.generateBtn.disabled = !enabled;
        this.previewBtn.disabled = !enabled;
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
                createZip: this.createZipCheckbox ? this.createZipCheckbox.checked : false
            };

            const payload = {
                structure: this.currentStructure,
                targetPath: this.folderPath,
                options: options
            };

            const endpoint = mode === 'preview' ? 'preview' : 'generate';
            
            const response = await fetch(`${this.apiUrl}/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (data.success || data.preview) {
                this.displayOutput(data, mode);
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
            
            // Afficher le bouton de téléchargement si un ZIP a été créé
            if (data.zipFile) {
                this.downloadZipBtn.style.display = 'inline-block';
                this.downloadZipBtn.dataset.file = data.zipFile;
            }
        }

        this.output.textContent = output;
        this.showOutput();
    }

    generatePreviewText() {
        let preview = '📋 APERÇU DE LA STRUCTURE\n';
        preview += '════════════════════════\n\n';

        this.currentStructure.forEach(item => {
            const indent = '  '.repeat(item.level);
            if (item.type === 'directory') {
                preview += `${indent}📁 ${item.name}/\n`;
            } else {
                preview += `${indent}📄 ${item.name}\n`;
            }
        });

        const dirs = this.currentStructure.filter(i => i.type === 'directory');
        const files = this.currentStructure.filter(i => i.type === 'file');

        preview += `\nTotal: ${dirs.length} dossiers, ${files.length} fichiers`;
        return preview;
    }

    generateSuccessMessage(data) {
        let message = '✅ STRUCTURE GÉNÉRÉE AVEC SUCCÈS\n';
        message += '════════════════════════════════\n\n';
        
        message += `📁 Dossier de destination: ${this.folderPath}\n\n`;
        
        message += '📋 Structure créée:\n';
        this.currentStructure.forEach(item => {
            const indent = '  '.repeat(item.level);
            if (item.type === 'directory') {
                message += `${indent}📁 ${item.path}\n`;
            } else {
                message += `${indent}📄 ${item.path}\n`;
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
            .then(() => this.showTemporaryMessage('Copié !'))
            .catch(() => alert('Erreur de copie'));
    }

    clearOutput() {
        this.output.textContent = '';
        this.outputSection.style.display = 'none';
        this.downloadZipBtn.style.display = 'none';
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
    }

    hideLoading() {
        this.generateBtn.innerHTML = '<span class="btn-icon">⚡</span> Générer la structure';
        this.generateBtn.disabled = !(this.currentStructure && this.folderPath);
        this.previewBtn.disabled = !(this.currentStructure && this.folderPath);
    }

    showError(message) {
        this.output.textContent = `❌ ${message}`;
        this.showOutput();
    }

    showTemporaryMessage(message) {
        const originalText = this.copyOutputBtn.textContent;
        this.copyOutputBtn.textContent = message;
        setTimeout(() => {
            this.copyOutputBtn.textContent = originalText;
        }, 2000);
    }
}

// Initialiser l'application
document.addEventListener('DOMContentLoaded', () => {
    new FileStructureGenerator();
});