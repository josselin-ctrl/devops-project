#!/bin/bash
# 01-ressources-du-projet.sh — Préparer l'AWS local au démarrage
#
# Ce script est exécuté AUTOMATIQUEMENT par Floci, une fois qu'il est prêt à
# répondre. C'est ce qu'on appelle un "hook d'initialisation".
#
# À quoi ça sert ? À ce que ton environnement soit toujours dans le même état
# au démarrage, sans que tu aies à taper des commandes à la main. C'est un
# principe DevOps central : si tu fais quelque chose plus de deux fois à la
# main, tu le scriptes.
#
# Floci connaît 4 moments (chacun son dossier) :
#   boot.d   → tout au début, avant même que le stockage soit chargé
#   start.d  → quand le serveur HTTP commence à répondre
#   ready.d  → quand TOUT est prêt  ← c'est ici qu'on est
#   stop.d   → à l'arrêt

set -e  # Arrête le script à la première erreur (voir Module 1)

ENDPOINT="http://localhost:4566"

echo "→ Préparation des ressources AWS du projet..."

# --- Un bucket S3 pour les pièces jointes des tâches ---
# Un "bucket" = un espace de stockage de fichiers (le "dossier racine" de S3).
aws --endpoint-url "$ENDPOINT" s3 mb s3://taskflow-pieces-jointes 2>/dev/null \
  && echo "  ✓ bucket S3 'taskflow-pieces-jointes' créé" \
  || echo "  · bucket S3 déjà présent"

# --- Une file d'attente SQS pour les traitements longs ---
# Une "file" (queue) = une liste de messages à traiter plus tard, sans faire
# attendre l'utilisateur. Voir la section SQS du Module 5.
aws --endpoint-url "$ENDPOINT" sqs create-queue --queue-name taskflow-traitements >/dev/null 2>&1 \
  && echo "  ✓ file SQS 'taskflow-traitements' créée" \
  || echo "  · file SQS déjà présente"

# --- Un bucket pour le state Terraform (Module 6) ---
aws --endpoint-url "$ENDPOINT" s3 mb s3://taskflow-tfstate 2>/dev/null \
  && echo "  ✓ bucket S3 'taskflow-tfstate' créé (state Terraform)" \
  || echo "  · bucket tfstate déjà présent"

echo "→ AWS local prêt à l'emploi."
