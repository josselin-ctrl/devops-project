# aws_client.py — Comment on parle à AWS depuis du code Python
#
# ─── LE PROBLÈME QU'ON RÉSOUT ICI ───
#
# Ton code a besoin de parler à AWS (déposer un fichier sur S3, envoyer un message
# dans une file SQS...). En production, il parle au vrai AWS. Mais sur ta machine
# et dans la CI, tu ne veux PAS parler au vrai AWS :
#   - il faudrait un compte et une carte bancaire,
#   - ça coûte de l'argent,
#   - les tests de plusieurs personnes se marcheraient dessus,
#   - et il faudrait mettre de vrais secrets AWS dans GitHub.
#
# ─── LA SOLUTION : LA VARIABLE AWS_ENDPOINT_URL ───
#
# Un "endpoint", c'est l'adresse à laquelle on envoie les requêtes.
# Par défaut, boto3 (la librairie AWS pour Python) envoie tout au vrai AWS.
# Si on lui donne une autre adresse, il envoie tout là-bas à la place.
#
#   AWS_ENDPOINT_URL absente          → le code parle au VRAI AWS      (production)
#   AWS_ENDPOINT_URL=http://...:4566  → le code parle à Floci en local (dev + CI)
#
# Le code ci-dessous ne change JAMAIS entre les environnements.
# Seule la configuration change. C'est exactement le principe que tu as vu au
# Module 1 avec les environnements dev / staging / prod.

import os

import boto3

# os.getenv("X") renvoie la valeur de la variable d'environnement X,
# ou None si elle n'existe pas.
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")


def get_client(service_name: str):
    """Crée un client boto3 pour un service AWS (ex: "s3", "sqs").

    Si AWS_ENDPOINT_URL est définie, le client tape sur cette adresse
    (Floci en local) au lieu du vrai AWS.
    """
    # Les paramètres communs, quel que soit l'environnement
    kwargs = {
        "region_name": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    }

    if AWS_ENDPOINT_URL:
        # --- Mode local (Floci) ---
        # On ajoute l'adresse locale et des identifiants factices.
        # Floci accepte n'importe quels identifiants : il ne vérifie pas les
        # permissions, il vérifie juste que la requête est bien formée.
        kwargs["endpoint_url"] = AWS_ENDPOINT_URL
        kwargs["aws_access_key_id"] = os.getenv("AWS_ACCESS_KEY_ID", "test")
        kwargs["aws_secret_access_key"] = os.getenv("AWS_SECRET_ACCESS_KEY", "test")

    # --- Mode production (vrai AWS) ---
    # On ne passe aucun identifiant : boto3 les trouve tout seul, dans l'ordre :
    #   1. les variables d'environnement AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
    #   2. le fichier ~/.aws/credentials (créé par `aws configure`)
    #   3. le rôle IAM de la machine EC2 / du container ECS (le plus sûr en prod :
    #      aucun secret n'est stocké nulle part, AWS les fournit automatiquement)

    return boto3.client(service_name, **kwargs)


def deposer_fichier(bucket: str, cle: str, contenu: bytes) -> None:
    """Dépose un fichier dans un bucket S3.

    bucket = le "dossier racine" S3, cle = le chemin du fichier dedans.
    """
    get_client("s3").put_object(Bucket=bucket, Key=cle, Body=contenu)


def lire_fichier(bucket: str, cle: str) -> bytes:
    """Relit un fichier déposé sur S3 et renvoie son contenu."""
    reponse = get_client("s3").get_object(Bucket=bucket, Key=cle)
    return reponse["Body"].read()


def empiler_tache(queue_url: str, message: str) -> str:
    """Dépose un message dans une file d'attente SQS.

    Renvoie l'identifiant du message. L'appelant n'attend PAS que le message
    soit traité — c'est tout l'intérêt d'une file : répondre immédiatement.
    """
    reponse = get_client("sqs").send_message(QueueUrl=queue_url, MessageBody=message)
    return reponse["MessageId"]
