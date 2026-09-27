# Dockerfile du backend — Construit l'image Docker pour l'API FastAPI
# Build : docker build -t devops-backend .
# Run   : docker run -p 8000:8000 devops-backend

# Image de base : Python 3.12 en version légère (slim = sans les outils inutiles)
FROM python:3.12-slim

# Copier uv (gestionnaire de dépendances Python) depuis son image officielle
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Définir le dossier de travail dans le container
WORKDIR /app

# Copier d'abord les fichiers de dépendances, puis les installer
# Astuce : on copie ces fichiers AVANT le code source
# → Docker cache cette étape et ne réinstalle les dépendances que si elles changent
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
# --frozen = utiliser exactement les versions du uv.lock (pas de mise à jour)
# --no-dev = ne pas installer les dépendances de dev (pytest, ruff, etc.)

# Copier le code source de l'application
COPY . .

# Documenter le port utilisé (ne l'ouvre pas réellement, c'est informatif)
EXPOSE 8000

# Commande lancée quand le container démarre
# uvicorn = le serveur HTTP qui fait tourner FastAPI
# --host 0.0.0.0 = écouter sur toutes les interfaces (nécessaire dans Docker)
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
