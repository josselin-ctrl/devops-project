# main.py — Le backend (API) de l'application Task List
# Ce fichier définit tous les endpoints HTTP que le frontend appelle.
# Framework utilisé : FastAPI (Python)

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# Modèle de validation : quand on crée une tâche, on exige un champ "title"
# FastAPI valide automatiquement le JSON reçu et retourne 422 si c'est invalide
class TaskCreate(BaseModel):
    title: str


# ---------------------------------------------------------------------------
# Storage : PostgreSQL si DATABASE_URL est défini, sinon in-memory
# ---------------------------------------------------------------------------
# Ce pattern permet d'utiliser le même code dans 2 contextes :
# - En local (sans Docker) : pas de DATABASE_URL → stockage en mémoire (liste Python)
# - Avec Docker Compose  : DATABASE_URL défini → connexion à PostgreSQL
# On ne modifie jamais le code entre les environnements, seulement la config.

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # --- Mode PostgreSQL ---
    import psycopg2  # Librairie pour se connecter à PostgreSQL

    def _conn():
        """Ouvre une connexion à la base de données."""
        return psycopg2.connect(DATABASE_URL)

    def _init_db():
        """Crée la table 'tasks' au démarrage si elle n'existe pas."""
        with _conn() as conn:
            with conn.cursor() as cur:
                # CREATE TABLE IF NOT EXISTS = ne crée que si la table n'existe pas
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        done BOOLEAN DEFAULT FALSE
                    )
                """)
                # Insérer des tâches de démo si la table est vide
                cur.execute("SELECT COUNT(*) FROM tasks")
                if cur.fetchone()[0] == 0:
                    cur.execute(
                        "INSERT INTO tasks (title) VALUES "
                        "('Apprendre Docker'), ('Configurer CI/CD')"
                    )

    def _list_tasks():
        """Récupère toutes les tâches depuis PostgreSQL."""
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, title, done FROM tasks ORDER BY id")
                return [{"id": r[0], "title": r[1], "done": r[2]} for r in cur.fetchall()]

    def _add_task(title):
        """Ajoute une tâche dans PostgreSQL et retourne la tâche créée."""
        with _conn() as conn:
            with conn.cursor() as cur:
                # RETURNING = récupère la ligne insérée (avec l'id généré)
                cur.execute(
                    "INSERT INTO tasks (title) VALUES (%s) RETURNING id, title, done", (title,)
                )
                r = cur.fetchone()
                return {"id": r[0], "title": r[1], "done": r[2]}

    def _toggle_task(task_id):
        """Inverse le statut done/not done d'une tâche."""
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE tasks SET done = NOT done WHERE id = %s "
                    "RETURNING id, title, done",
                    (task_id,),
                )
                r = cur.fetchone()
                if not r:
                    raise HTTPException(status_code=404, detail="Task not found")
                return {"id": r[0], "title": r[1], "done": r[2]}

    def _remove_task(task_id):
        """Supprime une tâche par son ID. Retourne 404 si elle n'existe pas."""
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Task not found")

else:
    # --- Mode in-memory (sans base de données) ---
    # Les données sont stockées dans une simple liste Python
    # Pratique pour développer et tester sans installer PostgreSQL
    _tasks: list[dict] = [
        {"id": 1, "title": "Apprendre Docker", "done": False},
        {"id": 2, "title": "Configurer CI/CD", "done": False},
    ]
    _next_id = 3  # Compteur pour générer des IDs uniques

    def _init_db():
        """Rien à préparer en mode in-memory — la liste existe déjà."""
        pass

    def _list_tasks():
        return _tasks

    def _add_task(title):
        global _next_id  # global = utiliser la variable définie en dehors de la fonction
        task = {"id": _next_id, "title": title, "done": False}
        _next_id += 1
        _tasks.append(task)
        return task

    def _toggle_task(task_id):
        for t in _tasks:
            if t["id"] == task_id:
                t["done"] = not t["done"]  # Inverse True ↔ False
                return t
        raise HTTPException(status_code=404, detail="Task not found")

    def _remove_task(task_id):
        for i, t in enumerate(_tasks):  # enumerate = parcourir avec l'index
            if t["id"] == task_id:
                _tasks.pop(i)  # Retirer l'élément à l'index i
                return
        raise HTTPException(status_code=404, detail="Task not found")


# ---------------------------------------------------------------------------
# Lifespan — Ce qui se passe au démarrage et à l'arrêt de l'application
# ---------------------------------------------------------------------------
# Une application a un cycle de vie : elle démarre, elle travaille, elle s'arrête.
# Le "lifespan" te permet d'exécuter du code à ces deux moments précis :
#   - AVANT le `yield`  → au démarrage (ici : créer la table si elle n'existe pas)
#   - APRÈS le `yield`  → à l'arrêt (ici : rien, mais on fermerait des connexions,
#                          on viderait un cache, on préviendrait un service...)
#
# Pourquoi c'est important en DevOps ? Parce que ton container peut être redémarré
# à tout moment (déploiement, crash, scaling). Le code de démarrage doit donc être
# "idempotent" : le relancer 100 fois doit donner le même résultat qu'une seule fois.
# C'est pour ça qu'on écrit CREATE TABLE **IF NOT EXISTS**.


@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_db()  # ← au démarrage
    yield  # ← l'application tourne pendant tout ce temps
    # ← à l'arrêt (rien à nettoyer ici)


# Créer l'application FastAPI, en lui donnant son cycle de vie
app = FastAPI(lifespan=lifespan)

# CORS = Cross-Origin Resource Sharing
# Permet au frontend (port 3000 en dev) d'appeler le backend (port 8000)
# Sans ça, le navigateur bloque les requêtes entre domaines/ports différents
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # "*" = tout le monde peut appeler l'API (OK pour le dev)
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes — Les endpoints HTTP que le frontend appelle
# ---------------------------------------------------------------------------
# Chaque décorateur (@app.get, @app.post, etc.) associe une URL à une fonction.
# FastAPI génère automatiquement la doc sur http://localhost:8000/docs


@app.get("/")
def root():
    """GET / → Page d'accueil de l'API. Si tu vois ce message dans ton navigateur,
    c'est que le backend tourne correctement et que tu communiques directement avec lui."""
    return {
        "message": "L'API Task List fonctionne !",
        "info": "Tu es en train de voir une réponse renvoyée par le backend (FastAPI).",
        "endpoints": {
            "GET /api/tasks": "Liste toutes les tâches",
            "POST /api/tasks": "Crée une tâche",
            "PATCH /api/tasks/{id}": "Coche/décoche une tâche",
            "DELETE /api/tasks/{id}": "Supprime une tâche",
            "GET /api/health": "Health check",
        },
        "documentation": "http://localhost:8000/docs",
    }


@app.get("/api/tasks")
def get_tasks():
    """GET /api/tasks → Retourne la liste de toutes les tâches."""
    return _list_tasks()


@app.post("/api/tasks", status_code=201)
def create_task(task: TaskCreate):
    """POST /api/tasks → Crée une nouvelle tâche. Body: {"title": "..."}"""
    return _add_task(task.title)


@app.patch("/api/tasks/{task_id}")
def toggle_task(task_id: int):
    """PATCH /api/tasks/1 → Inverse done/not done de la tâche 1."""
    return _toggle_task(task_id)


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """DELETE /api/tasks/1 → Supprime la tâche 1."""
    _remove_task(task_id)


@app.get("/api/health")
def health():
    """GET /api/health → Health check. Utilisé par Docker, Kubernetes, et les load balancers
    pour vérifier que l'application répond."""
    return {"status": "ok"}
