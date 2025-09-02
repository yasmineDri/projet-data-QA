#!/bin/bash
set -e

echo "🚀 Déploiement du projet QualAir..."

# Arrêter et supprimer les anciens conteneurs
docker-compose down

# Rebuild et relance de l’infra
docker-compose up -d --build

echo "✅ Déploiement terminé !"
