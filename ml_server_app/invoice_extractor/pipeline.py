import os
import cv2
import numpy as np
import pytesseract
from PIL import Image
import spacy
import json
from pathlib import Path
import re
from datetime import datetime
import logging

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chargement du modèle spaCy
try:
    nlp = spacy.load("fr_core_news_md")
except:
    logger.warning("Modèle spaCy fr_core_news_md non trouvé. Utilisation du modèle par défaut.")
    nlp = spacy.load("en_core_web_sm")

class InvoiceExtractionPipeline:
    """Pipeline d'extraction d'informations à partir de factures"""
    
    def __init__(self, base_dir=None):
        """
        Initialise le pipeline d'extraction
        
        Args:
            base_dir: Répertoire de base pour les modèles et les données
        """
        self.base_dir = base_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Chemins vers les datasets téléchargés
        self.datasets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'datasets')
        self.funsd_dir = os.path.join(self.datasets_dir, 'funsd', 'dataset')
        self.invoice2data_dir = os.path.join(self.datasets_dir, 'invoice2data', 'invoice2data-master')
        
        # Règles d'extraction communes
        self.common_patterns = {
            'amount': r'(?:total|montant|somme)(?:\s+(?:ttc|ht))?\s*:?\s*(?:€|EUR|euro)?\s*([0-9]+[.,][0-9]{2})',
            'date': r'(?:date|émis le|du)\s*:?\s*([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})',
            'invoice_number': r'(?:facture|invoice|n°|numéro)\s*:?\s*([A-Za-z0-9-]+)',
            'tax': r'(?:tva|tax|taxe)\s*:?\s*(?:€|EUR|euro)?\s*([0-9]+[.,][0-9]{2})',
        }
    
    def preprocess_image(self, image_path):
        """
        Prétraite l'image pour améliorer la qualité de l'OCR
        
        Args:
            image_path: Chemin vers l'image à prétraiter
            
        Returns:
            Image prétraitée
        """
        # Chargement de l'image
        image = cv2.imread(image_path)
        
        # Conversion en niveaux de gris
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Débruitage
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Binarisation adaptative
        binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        return binary
    
    def extract_text_from_image(self, image):
        """
        Extrait le texte d'une image à l'aide de Tesseract OCR
        
        Args:
            image: Image prétraitée
            
        Returns:
            Texte extrait
        """
        # Configuration de Tesseract pour le français
        custom_config = r'--oem 3 --psm 6 -l fra+eng'
        
        # Conversion de l'image OpenCV en image PIL
        pil_image = Image.fromarray(image)
        
        # Extraction du texte
        text = pytesseract.image_to_string(pil_image, config=custom_config)
        
        return text
    
    def extract_text_from_pdf(self, pdf_path):
        """
        Extrait le texte d'un PDF
        
        Args:
            pdf_path: Chemin vers le PDF
            
        Returns:
            Texte extrait
        """
        # Utilisation de pytesseract pour extraire le texte des PDFs scannés
        # Dans un cas réel, on utiliserait pdfplumber ou PyPDF2 pour les PDFs textuels
        # et pytesseract pour les PDFs scannés
        
        # Pour cet exemple, on suppose que c'est un PDF scanné
        from pdf2image import convert_from_path
        
        # Conversion du PDF en images
        pages = convert_from_path(pdf_path)
        
        # Extraction du texte de chaque page
        text = ""
        for page in pages:
            text += pytesseract.image_to_string(page, config=r'--oem 3 --psm 6 -l fra+eng')
            text += "\n\n"
        
        return text
    
    def extract_entities_with_spacy(self, text):
        """
        Extrait les entités nommées à l'aide de spaCy
        
        Args:
            text: Texte à analyser
            
        Returns:
            Entités extraites
        """
        doc = nlp(text)
        
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)
        
        return entities
    
    def extract_with_regex(self, text):
        """
        Extrait les informations à l'aide d'expressions régulières
        
        Args:
            text: Texte à analyser
            
        Returns:
            Informations extraites
        """
        results = {}
        
        # Extraction avec les patterns communs
        for key, pattern in self.common_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                results[key] = matches[0]
        
        return results
    
    def extract_line_items(self, text):
        """
        Extrait les lignes de facture
        
        Args:
            text: Texte à analyser
            
        Returns:
            Lignes de facture extraites
        """
        # Cette fonction est simplifiée pour l'exemple
        # Dans un cas réel, on utiliserait des techniques plus avancées
        
        # Recherche de tableaux ou de lignes de produits
        lines = []
        
        # Pattern simple pour détecter les lignes de produits
        pattern = r'(\d+)\s+([A-Za-z0-9\s]+)\s+(\d+[.,]\d{2})\s+(\d+[.,]\d{2})'
        matches = re.findall(pattern, text)
        
        for match in matches:
            if len(match) >= 4:
                lines.append({
                    'quantity': match[0],
                    'description': match[1].strip(),
                    'unit_price': match[2],
                    'total_price': match[3]
                })
        
        return lines
    
    def process_invoice(self, file_path):
        """
        Traite une facture et extrait les informations
        
        Args:
            file_path: Chemin vers le fichier de facture
            
        Returns:
            Informations extraites
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Extraction du texte selon le type de fichier
        if file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            # Prétraitement de l'image
            preprocessed = self.preprocess_image(file_path)
            # Extraction du texte
            text = self.extract_text_from_image(preprocessed)
        elif file_ext == '.pdf':
            # Extraction du texte du PDF
            text = self.extract_text_from_pdf(file_path)
        else:
            raise ValueError(f"Format de fichier non pris en charge: {file_ext}")
        
        # Extraction des entités avec spaCy
        entities = self.extract_entities_with_spacy(text)
        
        # Extraction avec regex
        regex_results = self.extract_with_regex(text)
        
        # Extraction des lignes de facture
        line_items = self.extract_line_items(text)
        
        # Combinaison des résultats
        results = {
            'text': text,
            'entities': entities,
            **regex_results,
            'line_items': line_items
        }
        
        # Formatage des résultats
        formatted_results = self.format_results(results)
        
        return formatted_results
    
    def format_results(self, results):
        """
        Formate les résultats extraits
        
        Args:
            results: Résultats bruts
            
        Returns:
            Résultats formatés
        """
        formatted = {
            'vendor_name': None,
            'invoice_number': results.get('invoice_number'),
            'invoice_date': None,
            'due_date': None,
            'total_amount': None,
            'tax_amount': results.get('tax'),
            'currency': 'EUR',  # Par défaut
            'line_items': results.get('line_items', [])
        }
        
        # Recherche du nom du fournisseur
        if 'ORG' in results.get('entities', {}):
            formatted['vendor_name'] = results['entities']['ORG'][0]
        
        # Formatage de la date
        if 'date' in results:
            try:
                # Tentative de parsing de la date
                date_str = results['date']
                # Détection du format de date
                if re.match(r'\d{1,2}[./-]\d{1,2}[./-]\d{4}', date_str):
                    # Format JJ/MM/AAAA
                    date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                elif re.match(r'\d{1,2}[./-]\d{1,2}[./-]\d{2}', date_str):
                    # Format JJ/MM/AA
                    date_obj = datetime.strptime(date_str, '%d/%m/%y')
                else:
                    date_obj = None
                
                if date_obj:
                    formatted['invoice_date'] = date_obj.strftime('%Y-%m-%d')
            except:
                pass
        
        # Formatage du montant
        if 'amount' in results:
            try:
                # Nettoyage et conversion du montant
                amount_str = results['amount'].replace(',', '.')
                formatted['total_amount'] = float(amount_str)
            except:
                pass
        
        return formatted
    
    def load_training_data(self, dataset_type='funsd'):
        """
        Charge les données d'entraînement
        
        Args:
            dataset_type: Type de dataset à charger ('funsd' ou 'invoice2data')
            
        Returns:
            Données d'entraînement
        """
        if dataset_type == 'funsd':
            return self._load_funsd_data()
        elif dataset_type == 'invoice2data':
            return self._load_invoice2data_data()
        else:
            raise ValueError(f"Type de dataset non pris en charge: {dataset_type}")
    
    def _load_funsd_data(self):
        """
        Charge les données du dataset FUNSD
        
        Returns:
            Données du dataset FUNSD
        """
        training_data = []
        
        # Chargement des données d'entraînement
        training_dir = os.path.join(self.funsd_dir, 'training_data')
        
        # Parcours des annotations
        annotations_dir = os.path.join(training_dir, 'annotations')
        images_dir = os.path.join(training_dir, 'images')
        
        for filename in os.listdir(annotations_dir):
            if filename.endswith('.json'):
                # Chargement des annotations
                with open(os.path.join(annotations_dir, filename), 'r') as f:
                    annotation = json.load(f)
                
                # Chemin vers l'image correspondante
                image_path = os.path.join(images_dir, filename.replace('.json', '.png'))
                
                if os.path.exists(image_path):
                    training_data.append({
                        'image_path': image_path,
                        'annotation': annotation
                    })
        
        return training_data
    
    def _load_invoice2data_data(self):
        """
        Charge les données du dataset Invoice2Data
        
        Returns:
            Données du dataset Invoice2Data
        """
        training_data = []
        
        # Chargement des données de test
        test_dir = os.path.join(self.invoice2data_dir, 'tests', 'compare')
        
        for filename in os.listdir(test_dir):
            if filename.endswith('.pdf') or filename.endswith('.png'):
                # Recherche du fichier JSON correspondant
                json_path = os.path.join(test_dir, filename.replace('.pdf', '.json').replace('.png', '.json'))
                
                if os.path.exists(json_path):
                    # Chargement des annotations
                    with open(json_path, 'r') as f:
                        annotation = json.load(f)
                    
                    training_data.append({
                        'image_path': os.path.join(test_dir, filename),
                        'annotation': annotation
                    })
        
        return training_data
    
    def train_model(self, training_data, model_name='invoice_extractor'):
        """
        Entraîne un modèle d'extraction
        
        Args:
            training_data: Données d'entraînement
            model_name: Nom du modèle
            
        Returns:
            Modèle entraîné
        """
        # Cette fonction est un placeholder pour l'entraînement du modèle
        # Dans un cas réel, on utiliserait des techniques d'apprentissage automatique
        
        logger.info(f"Entraînement du modèle {model_name} avec {len(training_data)} exemples")
        
        # Sauvegarde du modèle
        model_path = os.path.join(self.base_dir, f"{model_name}.pkl")
        
        # Dans un cas réel, on sauvegarderait le modèle entraîné
        with open(model_path, 'w') as f:
            f.write("Placeholder pour le modèle entraîné")
        
        return model_path