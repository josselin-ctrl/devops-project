# test_main.py — Tests automatisés pour l'API
# On utilise pytest + TestClient de FastAPI pour simuler des requêtes HTTP
# Lance les tests avec : uv run pytest

import pytest
from fastapi.testclient import TestClient

from main import app


# ─── Pourquoi une "fixture" et pas juste `client = TestClient(app)` ? ───
#
# Notre application a un "lifespan" (voir main.py) : du code qui doit s'exécuter
# à son démarrage — en l'occurrence, créer la table `tasks` en base.
#
# Ce code de démarrage ne se déclenche QUE si on utilise le TestClient avec
# `with` (un "context manager", comme `with open(...)` pour un fichier).
# Écrit sans `with`, les tests marcheraient en mémoire mais échoueraient dès
# qu'on les lance contre une vraie base : la table n'aurait jamais été créée.
#
# Une "fixture" pytest, c'est du décor préparé avant chaque test. Ici elle
# ouvre le client, le prête au test, puis le referme proprement.
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c  # ← le test s'exécute ici, avec `c` comme client


def test_get_tasks(client):
    """Vérifie que GET /api/tasks retourne une liste de tâches."""
    response = client.get("/api/tasks")
    assert response.status_code == 200  # 200 = OK
    assert isinstance(response.json(), list)  # La réponse est une liste
    assert len(response.json()) >= 1  # Il y a au moins 1 tâche (les tâches de démo)


def test_create_task(client):
    """Vérifie que POST /api/tasks crée une tâche et retourne 201."""
    response = client.post("/api/tasks", json={"title": "Nouvelle tâche"})
    assert response.status_code == 201  # 201 = Created
    data = response.json()
    assert data["title"] == "Nouvelle tâche"
    assert data["done"] is False  # Une nouvelle tâche n'est pas terminée


def test_toggle_task(client):
    """Vérifie que PATCH /api/tasks/{id} inverse le statut done."""
    # Créer une tâche pour le test
    create = client.post("/api/tasks", json={"title": "À toggler"})
    task_id = create.json()["id"]

    # Premier toggle : False → True
    response = client.patch(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["done"] is True

    # Deuxième toggle : True → False
    response = client.patch(f"/api/tasks/{task_id}")
    assert response.json()["done"] is False


def test_toggle_task_not_found(client):
    """Vérifie que PATCH sur un ID inexistant retourne 404."""
    response = client.patch("/api/tasks/99999")
    assert response.status_code == 404  # 404 = Not Found


def test_delete_task(client):
    """Vérifie que DELETE /api/tasks/{id} supprime bien la tâche."""
    # Créer une tâche puis la supprimer
    create = client.post("/api/tasks", json={"title": "À supprimer"})
    task_id = create.json()["id"]

    response = client.delete(f"/api/tasks/{task_id}")
    assert response.status_code == 204  # 204 = No Content (supprimé, rien à retourner)

    # Vérifier qu'elle n'existe plus dans la liste
    tasks = client.get("/api/tasks").json()
    assert all(t["id"] != task_id for t in tasks)


def test_delete_task_not_found(client):
    """Vérifie que DELETE sur un ID inexistant retourne 404."""
    response = client.delete("/api/tasks/99999")
    assert response.status_code == 404


def test_health(client):
    """Vérifie que le health check répond OK."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
