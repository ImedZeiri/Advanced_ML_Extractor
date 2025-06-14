# Advanced ML Extractor

Application d'extraction intelligente d'informations à partir de factures utilisant le Machine Learning et la Computer Vision.

## Description

Advanced ML Extractor est une application backend Django qui automatise l'extraction d'informations à partir de factures au format PDF, image ou PDF scanné. Elle combine des techniques de NLP (Natural Language Processing) et de Computer Vision pour analyser et extraire les données pertinentes des factures.

## Fonctionnalités

- Détection du type de document
- Nettoyage et découpage des zones pertinentes
- OCR (Optical Character Recognition) avec Tesseract
- Analyse avancée avec des modèles NLP (spaCy, BERT)
- Analyse spatiale avec des modèles de Computer Vision (CNN)
- Système d'annotation de données
- Classification et matching avec des templates
- Vérification par règles métier
- API REST pour l'intégration avec d'autres systèmes

## Architecture

Le projet est organisé comme suit :

- `ml_server_app/` : Application Django principale
  - `invoice_extractor/` : Application Django pour l'extraction de factures
  - `ml_server_app/` : Configuration du projet Django
- `datasets/` : Datasets utilisés pour l'entraînement et les tests
  - `funsd/` : Dataset FUNSD (Form Understanding in Noisy Scanned Documents)
  - `invoice2data/` : Dataset Invoice2Data

## Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/votre-utilisateur/Advanced_ML_Extractor.git
cd Advanced_ML_Extractor
```

2. Créer un environnement virtuel et l'activer :
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
```

3. Installer les dépendances :
```bash
pip install -r ml_server_app/requirements.txt
```

4. Installer Tesseract OCR :
   - Sur macOS : `brew install tesseract`
   - Sur Ubuntu : `sudo apt-get install tesseract-ocr`
   - Sur Windows : Télécharger et installer depuis [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)

5. Installer les modèles spaCy :
```bash
python -m spacy download fr_core_news_md
python -m spacy download en_core_web_sm
```

6. Appliquer les migrations :
```bash
cd ml_server_app
python manage.py migrate
```

7. Créer un superutilisateur :
```bash
python manage.py createsuperuser
```

## Utilisation

1. Démarrer le serveur Django :
```bash
cd ml_server_app
python manage.py runserver
```

2. Accéder à l'interface d'administration :
   - URL : [http://localhost:8000/admin/](http://localhost:8000/admin/)
   - Se connecter avec les identifiants du superutilisateur

3. Importer les datasets :
```bash
cd ml_server_app
python import_datasets.py
```

4. Utiliser l'API REST :
   - URL de base : [http://localhost:8000/api/](http://localhost:8000/api/)
   - Endpoints :
     - `/api/invoices/` : Gestion des factures
     - `/api/templates/` : Gestion des templates
     - `/api/training-data/` : Gestion des données d'entraînement

## Datasets

Le projet utilise deux datasets principaux :

1. **FUNSD** (Form Understanding in Noisy Scanned Documents) :
   - 398 documents scannés avec annotations
   - Formulaires, factures et reçus
   - Images au format PNG
   - Annotations au format JSON

2. **Invoice2Data** :
   - Exemples de factures avec annotations
   - Templates pour l'extraction d'informations
   - Factures au format PDF et PNG

## Licence

Ce projet est sous licence [MIT](LICENSE).

## Contact

Pour toute question ou suggestion, n'hésitez pas à nous contacter à l'adresse suivante : votre-email@example.com