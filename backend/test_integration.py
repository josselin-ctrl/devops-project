# test_integration.py — Tests d'INTÉGRATION (≠ tests unitaires)
#
# ─── QUELLE EST LA DIFFÉRENCE ? ───
#
# Test UNITAIRE (test_main.py) : on teste notre code TOUT SEUL, sans rien autour.
#   Rapide (millisecondes), aucune dépendance, tourne partout.
#
# Test d'INTÉGRATION (ce fichier) : on teste notre code AVEC les vrais services
#   auxquels il parle (ici S3 et SQS). Plus lent, mais c'est le seul moyen de
#   vérifier qu'on appelle correctement l'API d'AWS.
#
# Pourquoi les deux ? Parce qu'un test unitaire ne détecte pas qu'on s'est trompé
# de nom de paramètre dans un appel AWS — il ne fait jamais l'appel.
#
# ─── COMMENT LANCER CES TESTS ───
#
#   1. Démarre Floci :
#        cd devops-project/floci && docker compose up -d
#
#   2. Lance uniquement les tests d'intégration :
#        cd backend
#        AWS_ENDPOINT_URL=http://localhost:4566 uv run pytest -m integration
#
# Sans le `-m integration`, `uv run pytest` ne lance QUE les tests unitaires.
# C'est voulu : les tests rapides doivent pouvoir tourner sans rien installer.

import os
import uuid

import pytest

from aws_client import deposer_fichier, empiler_tache, get_client, lire_fichier

# @pytest.mark.integration = on "étiquette" tous les tests de ce fichier.
# L'étiquette est déclarée dans pyproject.toml, et exclue par défaut.
pytestmark = pytest.mark.integration


@pytest.fixture
def bucket():
    """Crée un bucket S3 neuf avant le test.

    Une "fixture" pytest, c'est du décor : ce qu'on prépare avant le test.
    On génère un nom unique (uuid) pour que deux tests lancés en même temps
    ne se marchent pas dessus — un réflexe important quand la CI parallélise.
    """
    nom = f"test-bucket-{uuid.uuid4().hex[:8]}"
    get_client("s3").create_bucket(Bucket=nom)
    return nom


@pytest.fixture
def queue_url():
    """Crée une file SQS neuve avant le test et renvoie son URL."""
    nom = f"test-queue-{uuid.uuid4().hex[:8]}"
    return get_client("sqs").create_queue(QueueName=nom)["QueueUrl"]


def test_endpoint_est_bien_configure():
    """Garde-fou : vérifie qu'on tape bien sur l'émulateur, pas sur le vrai AWS.

    Sans ce test, un oubli de variable enverrait les tests vers le vrai AWS —
    et l'erreur serait incompréhensible pour un débutant.
    """
    assert os.getenv("AWS_ENDPOINT_URL"), (
        "AWS_ENDPOINT_URL n'est pas définie : ces tests taperaient sur le VRAI AWS. "
        "Démarre Floci puis relance avec AWS_ENDPOINT_URL=http://localhost:4566"
    )


def test_depot_et_relecture_sur_s3(bucket):
    """Vérifie qu'un fichier déposé sur S3 se relit à l'identique."""
    deposer_fichier(bucket, "notes/rappel.txt", b"acheter du pain")

    contenu = lire_fichier(bucket, "notes/rappel.txt")

    assert contenu == b"acheter du pain"


def test_fichier_absent_leve_une_erreur(bucket):
    """Vérifie le cas d'erreur : lire un fichier qui n'existe pas doit échouer.

    Tester les cas qui ratent est aussi important que tester ceux qui marchent.
    """
    with pytest.raises(Exception):  # noqa: B017
        lire_fichier(bucket, "ce-fichier-nexiste-pas.txt")


def test_message_depose_dans_la_file(queue_url):
    """Vérifie qu'un message empilé dans SQS est bien récupérable ensuite."""
    message_id = empiler_tache(queue_url, "envoyer l'email de bienvenue")
    assert message_id  # SQS renvoie toujours un identifiant

    # On relit la file pour vérifier que le message y est vraiment
    recu = get_client("sqs").receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)

    assert recu["Messages"][0]["Body"] == "envoyer l'email de bienvenue"
