# DevOps Project — Task List

Application simple (frontend React + backend FastAPI) utilisée tout au long du cursus DevOps.

> En entreprise, le frontend et le backend sont généralement dans des dépôts (repos) séparés, avec chacun son propre pipeline CI/CD. Ici, on les met dans le même repo pour simplifier l'apprentissage.

## Architecture

```
┌──────────────┐     HTTP      ┌───────────────────┐     SQL       ┌──────────────┐
│              │   /api/...    │                   │               │              │
│   Frontend   │──────────────▶│     Backend       │──────────────▶│  PostgreSQL   │
│  (React +    │               │   (FastAPI +      │               │  (données)   │
│   nginx)     │◀──────────────│    Python)        │◀──────────────│              │
│              │     JSON      │                   │    rows       │              │
│   port 80    │               │    port 8000      │               │   port 5432  │
└──────────────┘               └───────────────────┘               └──────────────┘
       │                              │                                   │
       └──────────────────────────────┴───────────────────────────────────┘
                            Docker Compose (un réseau commun)
```

- Le **frontend** est une page web (React) servie par **nginx**. L'utilisateur voit la liste des tâches.
- **nginx** fait office de **reverse proxy** : les requêtes `/api` sont redirigées vers le backend.
- Le **backend** est une API Python (FastAPI). Il gère les tâches (créer, lister, toggler, supprimer).
- **PostgreSQL** stocke les données. Sans Docker (`DATABASE_URL` absente), le backend utilise une liste en mémoire.

## Structure

```
.github/workflows/
  ci.yml                    → Pipeline CI/CD (lint → test/intégration → build → push)
frontend/                   → Vite + React (géré par Bun)
  Dockerfile                → Multi-stage build (Bun → nginx)
  nginx.conf                → Reverse proxy vers le backend
backend/                    → Python FastAPI (géré par uv)
  Dockerfile                → Image Python avec uv
  main.py                   → L'API (routes + stockage)
  aws_client.py             → Le code qui parle à AWS (S3, SQS)
  test_main.py              → Tests unitaires
  test_integration.py       → Tests d'intégration (nécessitent Floci)
floci/                      → L'AWS local (émulateur, voir plus bas)
  docker-compose.yml        → Démarre Floci
  init/ready.d/             → Scripts exécutés au démarrage de Floci
docker-compose.yml          → Backend + Frontend + PostgreSQL
docker-compose.floci.yml    → Override : branche le backend sur l'AWS local
```

## Lancer en local (sans Docker)

**Backend :**
```bash
cd backend
uv sync
uv run uvicorn main:app --reload
# L'API tourne sur http://localhost:8000
# Sans DATABASE_URL → stockage in-memory (pas besoin de PostgreSQL)
```

**Frontend :**
```bash
cd frontend
bun install
bun run dev
# Le frontend tourne sur http://localhost:3000
# Les appels /api sont proxyfiés vers le backend
```

## Lancer avec Docker Compose

```bash
docker compose up -d --build
# Frontend : http://localhost (port 80)
# Backend :  http://localhost:8000
# PostgreSQL : port 5432 (accessible uniquement depuis le backend)
```

## Lancer l'AWS local (Floci)

**Floci** est un émulateur AWS : il imite AWS sur ta machine. Pas de compte, pas
de carte bancaire, pas de facture. C'est ce qui permet de pratiquer S3, SQS,
DynamoDB, Lambda, RDS, EC2 ou Terraform sans rien payer.

```bash
cd floci
docker compose up -d

# Vérifier que c'est prêt (doit répondre 200)
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:4566/health

# Toutes les commandes AWS pointent vers l'émulateur avec --endpoint-url
aws --endpoint-url http://localhost:4566 s3 ls
```

Pour brancher l'application dessus :

```bash
docker compose -f docker-compose.yml -f docker-compose.floci.yml up -d --build
```

Guide complet : [AWS en local avec Floci](../floci-aws-local.md).

## API Endpoints

| Méthode | URL | Description |
|---------|-----|-------------|
| `GET` | `/api/tasks` | Lister les tâches |
| `POST` | `/api/tasks` | Créer une tâche (`{"title": "..."}`) |
| `PATCH` | `/api/tasks/{id}` | Toggler done/not done |
| `DELETE` | `/api/tasks/{id}` | Supprimer une tâche |
| `GET` | `/api/health` | Health check |

## Linting

```bash
# Backend (Ruff)
cd backend && uv run ruff check .

# Frontend (Oxlint)
cd frontend && bunx oxlint .
```

## Tests

Il y a deux familles de tests, et elles ne se lancent pas pareil.

**Tests unitaires** — rapides, aucune dépendance :

```bash
cd backend && uv run pytest
# 7 tests : GET, POST, PATCH, PATCH 404, DELETE, DELETE 404, health
```

**Tests d'intégration** — ils parlent vraiment à S3 et SQS, donc il faut Floci :

```bash
cd floci && docker compose up -d && cd ../backend

AWS_ENDPOINT_URL=http://localhost:4566 uv run pytest -m integration
# 4 tests : dépôt/relecture S3, fichier absent, message SQS, garde-fou endpoint
```

Par défaut, `uv run pytest` **saute** les tests d'intégration (configuré dans
`pyproject.toml`). C'est voulu : les tests rapides doivent pouvoir tourner sans
rien installer.

**Les mêmes tests unitaires contre un vrai PostgreSQL** — le code ne change pas,
seule la variable d'environnement apparaît :

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/tasks uv run pytest
```
