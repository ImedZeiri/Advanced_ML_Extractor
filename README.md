# Extracteur ML de Factures

Application d'extraction intelligente d'informations à partir de factures en utilisant le Machine Learning, le NLP et la Computer Vision.

## Architecture

Le projet est composé de deux parties principales :

1. **Backend (Django + ML)** : API REST pour l'extraction d'informations à partir de factures
2. **Frontend (Angular)** : Interface utilisateur pour télécharger des factures et visualiser les résultats

## Fonctionnalités

- Upload de factures (PDF, images)
- Extraction automatique des informations clés (fournisseur, montant, date, etc.)
- Visualisation des résultats d'extraction
- API REST pour l'intégration avec d'autres systèmes

## Technologies utilisées

### Backend
- Django et Django REST Framework
- Tesseract OCR via Pytesseract
- OpenCV et Pillow pour le traitement d'images
- spaCy pour le NLP
- TensorFlow/PyTorch pour les modèles ML
- PDF2Image pour la conversion de PDF

### Frontend
- Angular avec Angular Material
- NgxFileDrop pour l'upload de fichiers

## Installation

### Prérequis
- Python 3.8+
- Node.js 14+
- Tesseract OCR

### Backend (Django)

1. Créer et activer un environnement virtuel :
```bash
./setup_venv.sh
```

2. Lancer le serveur Django :
```bash
cd ml_server_app
python manage.py runserver
```

### Frontend (Angular)

1. Installer les dépendances :
```bash
cd ml_client_app
npm install
```

2. Lancer le serveur de développement :
```bash
ng serve
```

3. Accéder à l'application dans votre navigateur : http://localhost:4200

## Structure du projet

```
Advanced_ML_Extractor/
├── data_source/                # Données d'exemple (factures)
├── ml_server_app/              # Application backend Django
│   ├── invoice_extractor/      # Application d'extraction de factures
│   └── ml_server_app/          # Configuration du projet Django
├── ml_client_app/              # Application frontend Angular
│   └── src/                    # Code source Angular
├── requirements.txt            # Dépendances Python
└── setup_venv.sh               # Script d'installation
```

## API REST

### Points d'entrée

- `POST /api/invoices/upload/` : Télécharger une facture
- `GET /api/invoices/{id}/results/` : Récupérer les résultats d'extraction
- `GET /api/invoices/` : Liste des factures
- `GET /api/invoices/{id}/` : Détails d'une facture

## Licence

Ce projet est sous licence MIT.