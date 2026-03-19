# Utiliser l'image Python officielle
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=server.py \
    FLASK_ENV=production

# Créer un utilisateur non-root
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /app/uploads /app/generated /app/static && \
    chown -R appuser:appuser /app

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

# Copier le code de l'application
COPY server.py tree_parser.py generator.py ./
COPY static/ ./static/

# Donner les permissions
RUN chown -R appuser:appuser /app

# Passer à l'utilisateur non-root
USER appuser

# Exposer le port
EXPOSE 5000

# Script d'entrée
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "server:app"]