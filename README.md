# Advanced ML Extractor pour Factures

Ce projet est une application d'extraction et de classification de factures utilisant des techniques avancées de Machine Learning, notamment LayoutLMv3, pour améliorer la précision de l'extraction des données.

## Fonctionnalités

- Extraction de texte à partir de factures (PDF, images)
- Classification et structuration des données avec LayoutLMv3
- Interface utilisateur pour corriger et annoter les données extraites
- Système d'apprentissage continu pour améliorer la précision au fil du temps
- API REST pour l'intégration avec d'autres systèmes

## Architecture

Le projet est composé de deux parties principales :

1. **Backend (Django + REST Framework)**
   - API pour l'extraction et la classification des factures
   - Modèle LayoutLMv3 pour l'extraction intelligente
   - Système d'annotation et d'apprentissage

2. **Frontend (Angular)**
   - Interface utilisateur pour télécharger et visualiser les factures
   - Édition des données extraites pour correction
   - Soumission des corrections pour entraîner le modèle

## Installation

### Prérequis

- Python 3.8+
- Node.js 14+
- Tesseract OCR
- Poppler (pour pdf2image)

### Installation automatique

Un script d'installation est fourni pour faciliter la mise en place de l'environnement :

```bash
python setup_layoutlmv3.py
```

Ce script va :
1. Vérifier la version de Python
2. Installer les dépendances requises
3. Vérifier l'installation de Tesseract OCR et Poppler
4. Télécharger le modèle LayoutLMv3 pré-entraîné
5. Appliquer les migrations Django

### Installation manuelle

#### Backend

```bash
cd ml_server_app
pip install -r ../requirements.txt
python manage.py migrate
python manage.py runserver
```

#### Frontend

```bash
cd ml_client_app
npm install
ng serve
```

### Installation de LayoutLMv3 (optionnel)

L'application peut fonctionner sans LayoutLMv3, mais avec des fonctionnalités réduites. Pour activer toutes les fonctionnalités d'IA avancée :

```bash
pip install torch transformers datasets
python -c "from transformers import LayoutLMv3Processor, LayoutLMv3ForTokenClassification; processor = LayoutLMv3Processor.from_pretrained('microsoft/layoutlmv3-base'); model = LayoutLMv3ForTokenClassification.from_pretrained('microsoft/layoutlmv3-base', num_labels=9); processor.save_pretrained('ml_server_app/invoice_api/models/layoutlmv3'); model.save_pretrained('ml_server_app/invoice_api/models/layoutlmv3')"
```

## Utilisation

1. Accédez à l'application via http://localhost:4200
2. Téléchargez une facture (PDF ou image)
3. Visualisez les données extraites automatiquement
4. Activez le mode édition pour corriger les données si nécessaire
5. Soumettez les corrections pour entraîner le modèle

## Résolution des problèmes courants

### LayoutLMv3 n'est pas disponible

Si vous voyez le message "IA avancée inactive" dans l'interface, cela signifie que LayoutLMv3 n'est pas correctement installé ou configuré. Utilisez le script d'installation ou suivez les instructions manuelles pour l'installer.

### Erreurs d'accès aux fichiers

Si vous rencontrez des erreurs d'accès aux fichiers lors de l'extraction ou de l'entraînement, assurez-vous que :
- Les fichiers PDF ne sont pas ouverts dans une autre application
- Vous avez les droits d'accès aux répertoires temporaires
- Vous avez suffisamment d'espace disque disponible

### Erreurs lors de l'entraînement

L'entraînement du modèle peut échouer pour plusieurs raisons :
- Mémoire insuffisante : LayoutLMv3 nécessite beaucoup de RAM
- GPU non disponible : l'entraînement est plus lent sur CPU
- Erreurs d'accès aux fichiers : voir ci-dessus

Vous pouvez vérifier le statut des jobs d'entraînement via l'API `/api/training-jobs/`.

## Modèle LayoutLMv3

LayoutLMv3 est un modèle multimodal qui combine la compréhension du texte et de la mise en page des documents. Il est particulièrement efficace pour l'extraction d'informations à partir de documents structurés comme les factures.

### Entraînement

Le modèle s'améliore au fil du temps grâce aux corrections apportées par les utilisateurs. Chaque correction est utilisée pour affiner le modèle et améliorer sa précision.

## API REST

L'API REST permet d'intégrer les fonctionnalités d'extraction et de classification dans d'autres applications.

### Endpoints principaux

- `POST /api/invoices/` : Télécharger et traiter une facture
- `GET /api/invoices/{id}/` : Récupérer les détails d'une facture
- `POST /api/invoices/{id}/annotate/` : Soumettre des corrections pour une facture
- `GET /api/ml/model-info/` : Obtenir des informations sur le modèle
- `GET /api/ml/export-annotations/` : Exporter toutes les annotations

## Licence

Ce projet est sous licence MIT.