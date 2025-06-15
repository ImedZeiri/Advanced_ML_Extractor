# Advanced ML Extractor

Application d'extraction et de traitement de texte à partir de factures et documents PDF.

## Fonctionnalités

- Extraction de texte à partir de PDF (textuels et scannés) et d'images
- Nettoyage et formatage du texte extrait
- Présentation visuelle améliorée des factures
- Extraction de données structurées (numéro de facture, date, montant)
- API REST pour l'intégration avec d'autres systèmes
- Interface utilisateur Angular pour le téléchargement et la visualisation

## Structure du projet

- `ml_server_app/` : Application backend Django avec API REST
  - `invoice_api/` : API pour l'extraction et le traitement des factures
  - `extractors.py` : Classes pour l'extraction et le traitement du texte
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

1. **Extraction** : Utilise PyPDF2 pour les PDF textuels et Tesseract OCR pour les PDF scannés et images
2. **Nettoyage** : Supprime les caractères indésirables et normalise les espaces
3. **Formatage** : Améliore la présentation visuelle en identifiant les sections importantes
4. **Extraction structurée** : Identifie les informations clés comme les numéros de facture, dates et montants
5. **Présentation** : Génère une version HTML formatée pour une meilleure lisibilité

## Installation et démarrage

1. Installer les dépendances :
```
pip install -r requirements.txt
```

2. Démarrer le serveur Django :
```
cd ml_server_app
python manage.py runserver
```

3. Démarrer l'application Angular :
```
cd ml_client_app
npm install
ng serve
```