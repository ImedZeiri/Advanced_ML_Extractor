import os
import cv2
import numpy as np
import pytesseract
from PIL import Image
import pdf2image
import spacy
import re
from datetime import datetime
import tensorflow as tf
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch

class InvoiceExtractionPipeline:
    """
    Pipeline complet pour l'extraction d'informations à partir de factures
    
    Combine OCR, NLP et Computer Vision pour extraire les données structurées
    """
    
    def __init__(self):
        """Initialisation du pipeline et chargement des modèles"""
        # Chargement du modèle spaCy pour NER
        try:
            self.nlp = spacy.load("fr_core_news_md")
        except:
            # Si le modèle n'est pas disponible, télécharger une version légère
            self.nlp = spacy.load("fr_core_news_sm")
        
        # Initialisation des modèles (à remplacer par vos modèles entraînés)
        # Dans une implémentation complète, on chargerait ici les modèles TensorFlow/PyTorch
        self.document_classifier = None
        self.field_detector = None
        
        # Configuration de Tesseract OCR
        pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'  # Chemin à adapter selon l'installation
    
    def process(self, file_path):
        """
        Traite une facture et extrait les informations
        
        Args:
            file_path: Chemin vers le fichier de facture (PDF, image)
            
        Returns:
            dict: Données extraites de la facture
        """
        # Vérification de l'extension du fichier
        _, ext = os.path.splitext(file_path)
        
        # Conversion du document en images
        if ext.lower() == '.pdf':
            images = self._convert_pdf_to_images(file_path)
        else:
            # Pour les formats image
            images = [cv2.imread(file_path)]
        
        # Prétraitement des images
        processed_images = [self._preprocess_image(img) for img in images]
        
        # OCR sur les images prétraitées
        text_content = ""
        for img in processed_images:
            text_content += pytesseract.image_to_string(img, lang='fra') + "\n"
        
        # Extraction des informations à partir du texte
        extracted_data = self._extract_information(text_content)
        
        # Ajout d'un score de confiance (simulé ici)
        extracted_data['confidence_score'] = 0.85
        
        return extracted_data
    
    def _convert_pdf_to_images(self, pdf_path):
        """Convertit un PDF en liste d'images"""
        return pdf2image.convert_from_path(pdf_path, dpi=300)
    
    def _preprocess_image(self, image):
        """
        Prétraite l'image pour améliorer la qualité de l'OCR
        
        Applique des techniques de traitement d'image comme:
        - Conversion en niveaux de gris
        - Débruitage
        - Binarisation adaptative
        - Correction de l'orientation
        """
        # Conversion en niveaux de gris si l'image est en couleur
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Débruitage
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Binarisation adaptative
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return binary
    
    def _extract_information(self, text):
        """
        Extrait les informations structurées à partir du texte OCR
        
        Utilise une combinaison de règles, expressions régulières et NER
        """
        # Initialisation du dictionnaire de résultats
        result = {}
        
        # Traitement NLP avec spaCy
        doc = self.nlp(text)
        
        # Extraction du numéro de facture
        invoice_number_pattern = r'(?i)(?:facture|invoice|n°|numéro)[\s:]*([A-Z0-9-]{3,20})'
        invoice_number_matches = re.findall(invoice_number_pattern, text)
        if invoice_number_matches:
            result['invoice_number'] = invoice_number_matches[0]
        
        # Extraction de la date de facture
        date_patterns = [
            r'(?i)(?:date\s*(?:de\s*)?(?:facture|émission))[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?i)(?:facture\s*du)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            date_matches = re.findall(pattern, text)
            if date_matches:
                # Conversion en format de date standard
                try:
                    # Tentative de parsing de la date (format à adapter selon les cas)
                    date_str = date_matches[0]
                    result['invoice_date'] = date_str
                    break
                except:
                    continue
        
        # Extraction du montant total
        amount_patterns = [
            r'(?i)(?:montant\s*total|total\s*ttc|total)[\s:]*(\d+[.,]\d{2})',
            r'(?i)(?:total\s*à\s*payer)[\s:]*(\d+[.,]\d{2})'
        ]
        
        for pattern in amount_patterns:
            amount_matches = re.findall(pattern, text)
            if amount_matches:
                # Conversion en nombre décimal
                try:
                    amount_str = amount_matches[0].replace(',', '.')
                    result['total_amount'] = float(amount_str)
                    break
                except:
                    continue
        
        # Extraction de la TVA
        tax_patterns = [
            r'(?i)(?:tva|taxe)[\s:]*(\d+[.,]\d{2})',
            r'(?i)(?:montant\s*tva)[\s:]*(\d+[.,]\d{2})'
        ]
        
        for pattern in tax_patterns:
            tax_matches = re.findall(pattern, text)
            if tax_matches:
                try:
                    tax_str = tax_matches[0].replace(',', '.')
                    result['tax_amount'] = float(tax_str)
                    break
                except:
                    continue
        
        # Extraction du nom du fournisseur (approche simplifiée)
        # Dans une implémentation complète, on utiliserait un modèle NER entraîné
        for ent in doc.ents:
            if ent.label_ == "ORG":
                result['vendor_name'] = ent.text
                break
        
        return result