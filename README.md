# Advanced ML Extractor

Application d'extraction et de traitement de texte à partir de factures et documents PDF utilisant des techniques avancées de ML et d'OCR.

## Fonctionnalités

- Extraction de texte à partir de PDF (textuels et scannés) et d'images
- Prétraitement d'image avancé pour améliorer la qualité de l'OCR
- Nettoyage et formatage du texte extrait
- Présentation visuelle améliorée des factures
- Extraction de données structurées (numéro de facture, date, montant)
- Validation et normalisation des données extraites
- Extraction avancée avec modèles de Machine Learning (NER)
- API REST pour l'intégration avec d'autres systèmes
- Interface utilisateur Angular pour le téléchargement et la visualisation
- Logging détaillé et métriques de confiance

## Nouvelles fonctionnalités

### Prétraitement d'image
- Redressement automatique des images inclinées
- Amélioration du contraste et de la netteté
- Réduction du bruit et binarisation adaptative
- Comparaison de différentes méthodes de prétraitement

### Extraction avancée
- Utilisation de modèles spaCy pour la reconnaissance d'entités nommées
- Intégration de modèles Transformers pour l'extraction d'informations
- Fusion des résultats de différentes méthodes d'extraction
- Métriques de confiance pour évaluer la qualité des extractions

### Validation des données
- Validation et normalisation des dates
- Validation et normalisation des montants
- Vérification de la cohérence des données extraites
- Score de confiance global pour les données extraites

## Structure du projet

- `ml_server_app/` : Application backend Django avec API REST
  - `invoice_api/` : API pour l'extraction et le traitement des factures
  - `extractors.py` : Classes pour l'extraction et le traitement du texte
  - `image_preprocessing.py` : Prétraitement d'image pour améliorer l'OCR
  - `ml_extractor.py` : Extraction avancée avec modèles de ML
  - `data_validation.py` : Validation et normalisation des données extraites
  - `text_utils.py` : Utilitaires pour la mise en forme du texte et la génération HTML
- `ml_client_app/` : Application frontend Angular
- `data_source/` : Exemples de factures pour les tests

## Utilisation de l'API

### Télécharger une facture

```
POST /api/invoices/
```

### Obtenir le texte formaté

```
GET /api/invoices/{id}/formatted_text/
```

### Obtenir le texte formaté en HTML

```
GET /api/invoices/{id}/formatted_text/?format=html
```

## Traitement du texte

Le système effectue les opérations suivantes sur le texte extrait :

1. **Prétraitement d'image** : Améliore la qualité des images avant l'OCR
2. **Extraction** : Utilise PyPDF2 pour les PDF textuels et Tesseract OCR pour les PDF scannés et images
3. **Nettoyage** : Supprime les caractères indésirables et normalise les espaces
4. **Formatage** : Améliore la présentation visuelle en identifiant les sections importantes
5. **Extraction structurée** : Identifie les informations clés comme les numéros de facture, dates et montants
6. **Extraction ML** : Utilise des modèles de ML pour extraire des informations supplémentaires
7. **Validation** : Valide et normalise les données extraites
8. **Présentation** : Génère une version HTML formatée pour une meilleure lisibilité

## Installation et démarrage

### Installation automatique

Utilisez le script d'installation pour configurer automatiquement le projet :

```
python setup.py
```

Ce script vérifie les dépendances système, installe les packages Python nécessaires et configure la base de données Django.

### Installation manuelle

1. Installer les dépendances système :
   - Tesseract OCR (pour l'OCR)
   - Poppler (pour la conversion PDF)

2. Installer les dépendances Python :
```
pip install -r requirements.txt
```

3. Installer les modèles spaCy :
```
python -m spacy download fr_core_news_lg
python -m spacy download en_core_web_lg
```

4. Configurer la base de données Django :
```
cd ml_server_app
python manage.py migrate
```

5. Démarrer le serveur Django :
```
python manage.py runserver
```

6. Démarrer l'application Angular :
```
cd ml_client_app
npm install
ng serve
```

## Configuration avancée

### Configuration de Tesseract OCR

Pour améliorer les résultats de l'OCR, vous pouvez configurer Tesseract avec des paramètres avancés dans `extractors.py` :

```python
custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
```

### Configuration des modèles ML

Les modèles ML peuvent être configurés dans `ml_extractor.py`. Vous pouvez changer les modèles utilisés ou ajuster les paramètres d'extraction.

### Patterns d'extraction

Les patterns d'extraction regex sont définis dans `regex_patterns.yaml`. Vous pouvez les modifier pour améliorer l'extraction des données spécifiques à vos factures.