#!/bin/bash

# Script pour configurer l'environnement virtuel et installer les dépendances

# Création de l'environnement virtuel
echo "Création de l'environnement virtuel..."
python3 -m venv venv

# Activation de l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source venv/bin/activate

# Installation des dépendances
echo "Installation des dépendances..."
pip install -r requirements.txt

# Installation du modèle français pour spaCy
echo "Téléchargement du modèle français pour spaCy..."
python -m spacy download fr_core_news_sm

# Migrations Django
echo "Application des migrations Django..."
cd ml_server_app
python manage.py makemigrations
python manage.py migrate

# Création d'un superutilisateur (optionnel)
echo "Voulez-vous créer un superutilisateur Django ? (o/n)"
read create_superuser
if [ "$create_superuser" = "o" ]; then
    python manage.py createsuperuser
fi

echo "Configuration terminée avec succès!"
echo "Pour lancer le serveur Django, exécutez: cd ml_server_app && python manage.py runserver"