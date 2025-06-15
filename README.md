# Advanced ML Extractor

Application d'extraction de texte à partir de factures (PDF et images) utilisant Django et Angular.

## Fonctionnalités

- Upload de factures (PDF texte, PDF scanné, images)
- Extraction automatique du texte
- Affichage des résultats au format JSON
- Interface utilisateur Angular

## Prérequis

- Python 3.8+
- Node.js et npm
- Tesseract OCR

## Installation

1. Cloner le dépôt
```bash
git clone <repository-url>
cd Advanced_ML_Extractor
```

2. Installer les dépendances Python
```bash
pip install -r requirements.txt
```

3. Installer Tesseract OCR
   - Sur macOS: `brew install tesseract`
   - Sur Ubuntu: `sudo apt-get install tesseract-ocr`
   - Sur Windows: Télécharger depuis https://github.com/UB-Mannheim/tesseract/wiki

4. Installer les dépendances Angular
```bash
cd ml_client_app
npm install
```

## Configuration

1. Assurez-vous que Tesseract est correctement installé et accessible dans le PATH
2. Vérifiez que les langues françaises et anglaises sont installées pour Tesseract

## Exécution

1. Démarrer le serveur Django
```bash
cd ml_server_app
python manage.py runserver
```

2. Démarrer l'application Angular
```bash
cd ml_client_app
ng serve
```

3. Accéder à l'application à l'adresse http://localhost:4200

## API Endpoints

- `POST /api/invoices/`: Upload d'une facture et extraction du texte
- `GET /api/invoices/`: Liste de toutes les factures
- `GET /api/invoices/{id}/`: Détails d'une facture spécifique
- `GET /api/invoices/{id}/extract/`: Réextraire le texte d'une facture existante

## Structure du projet

- `ml_client_app/`: Application frontend Angular
- `ml_server_app/`: Application backend Django
  - `invoice_api/`: API REST pour la gestion des factures
  - `extractors.py`: Module d'extraction de texte
- `data_source/`: Exemples de factures pour les tests