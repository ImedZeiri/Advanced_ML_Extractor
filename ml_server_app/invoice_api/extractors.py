import os
import tempfile
import re
from PIL import Image
import json

# Importations conditionnelles pour éviter les erreurs si certaines bibliothèques ne sont pas disponibles
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

class TextProcessor:
    """Classe pour nettoyer et formater le texte extrait des factures"""
    
    @staticmethod
    def clean_text(text):
        """
        Nettoie le texte extrait en supprimant les caractères indésirables
        et en normalisant les espaces
        
        Args:
            text: Texte brut extrait
            
        Returns:
            str: Texte nettoyé
        """
        if not text:
            return ""
            
        # Supprimer les caractères de contrôle sauf les sauts de ligne
        text = re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        # Normaliser les espaces multiples
        text = re.sub(r' +', ' ', text)
        
        # Normaliser les sauts de ligne multiples
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    @staticmethod
    def format_invoice_text(text):
        """
        Formate le texte pour qu'il ressemble davantage à la mise en page originale
        
        Args:
            text: Texte nettoyé
            
        Returns:
            str: Texte formaté
        """
        if not text:
            return ""
            
        # Identifier et mettre en évidence les sections importantes
        formatted_text = text
        
        # Mettre en évidence les montants
        formatted_text = re.sub(r'(\d+[,.]\d{2})\s*(€|EUR|EURO|EUROS)?', r'→ \1 € ←', formatted_text)
        
        # Identifier les dates (format JJ/MM/AAAA ou JJ-MM-AAAA)
        formatted_text = re.sub(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', r'Date: \1', formatted_text)
        
        # Identifier les numéros de facture potentiels
        formatted_text = re.sub(r'(?i)(facture|invoice|n°|numéro)[\s:]*([A-Z0-9-]{5,})', r'Numéro de facture: \2', formatted_text)
        
        # Ajouter des séparateurs pour améliorer la lisibilité
        lines = formatted_text.split('\n')
        result = []
        
        for line in lines:
            # Ajouter des séparateurs pour les lignes qui semblent être des en-têtes
            if line.isupper() and len(line) > 5:
                result.append('\n' + line + '\n' + '-' * len(line))
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    @staticmethod
    def extract_structured_data(text):
        """
        Extrait des données structurées à partir du texte de la facture
        
        Args:
            text: Texte nettoyé
            
        Returns:
            dict: Données structurées extraites
        """
        data = {
            "invoice_number": None,
            "date": None,
            "total_amount": None,
            "vendor": None,
            "items": [],
            "detected_fields": {}
        }
        
        # Extraire le numéro de facture
        invoice_match = re.search(r'(?i)(facture|invoice|n°|numéro)[\s:]*([A-Z0-9-]{5,})', text)
        if invoice_match:
            data["invoice_number"] = invoice_match.group(2)
        
        # Extraire la date
        date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
        if date_match:
            data["date"] = date_match.group(1)
        
        # Extraire le montant total
        amount_match = re.search(r'(?i)(total|montant|somme).*?(\d+[,.]\d{2})', text)
        if amount_match:
            data["total_amount"] = amount_match.group(2).replace(',', '.')
        
        # Détecter automatiquement les paires clé-valeur
        # Recherche des motifs comme "Clé: Valeur" ou "Clé = Valeur"
        key_value_patterns = [
            r'([A-Za-z0-9\s\-\']{3,30})\s*[:=]\s*([A-Za-z0-9\s\-\.,€\$£&@\'\/]{1,50})',  # Clé: Valeur ou Clé = Valeur
            r'([A-Za-z0-9\s\-\']{3,30})\s*[:|]\s*([A-Za-z0-9\s\-\.,€\$£&@\'\/]{1,50})',  # Variante avec | comme séparateur
        ]
        
        for pattern in key_value_patterns:
            for match in re.finditer(pattern, text):
                key = match.group(1).strip()
                value = match.group(2).strip()
                
                # Ignorer les clés trop courtes ou les valeurs vides
                if len(key) < 3 or not value:
                    continue
                    
                # Ignorer les clés qui sont des mots communs
                common_words = ['le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'pour', 'par']
                if key.lower() in common_words:
                    continue
                
                # Nettoyer la clé et la valeur
                key = key.strip().capitalize()
                value = value.strip()
                
                # Ajouter au dictionnaire des champs détectés
                data["detected_fields"][key] = value
        
        return data
    
    @staticmethod
    def process_extracted_text(extraction_result):
        """
        Traite le résultat d'extraction pour produire un texte propre et formaté
        
        Args:
            extraction_result: Dictionnaire contenant le texte extrait et des métadonnées
            
        Returns:
            dict: Dictionnaire contenant le texte original, nettoyé, formaté et les données structurées
        """
        if "error" in extraction_result:
            return extraction_result
            
        raw_text = extraction_result.get("text", "")
        
        # Nettoyer le texte
        cleaned_text = TextProcessor.clean_text(raw_text)
        
        # Formater le texte
        formatted_text = TextProcessor.format_invoice_text(cleaned_text)
        
        # Extraire des données structurées
        structured_data = TextProcessor.extract_structured_data(cleaned_text)
        
        # Ajouter les résultats au dictionnaire d'origine
        result = extraction_result.copy()
        result["cleaned_text"] = cleaned_text
        result["formatted_text"] = formatted_text
        result["structured_data"] = structured_data
        
        return result


class TextExtractor:
    """Classe pour extraire du texte à partir de différents types de documents"""
    
    @staticmethod
    def extract_from_file(file_path):
        """
        Extrait le texte d'un fichier en fonction de son type
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            dict: Dictionnaire contenant le texte extrait et des métadonnées
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        extraction_result = {}
        if file_ext == '.pdf':
            extraction_result = TextExtractor.extract_from_pdf(file_path)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            extraction_result = TextExtractor.extract_from_image(file_path)
        else:
            return {"error": "Format de fichier non pris en charge"}
            
        # Traiter le texte extrait pour le nettoyer et le formater
        return TextProcessor.process_extracted_text(extraction_result)
    
    @staticmethod
    def extract_from_pdf(pdf_path):
        """
        Extrait le texte d'un fichier PDF
        Essaie d'abord d'extraire le texte directement, puis utilise l'OCR si nécessaire
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            
        Returns:
            dict: Dictionnaire contenant le texte extrait et des métadonnées
        """
        # Vérifier si PyPDF2 est disponible
        if not PYPDF2_AVAILABLE:
            return {"error": "PyPDF2 n'est pas installé. Impossible d'extraire le texte du PDF."}
        
        # Essayer d'extraire le texte directement du PDF
        pdf_reader = PdfReader(pdf_path)
        text = ""
        
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        # Si du texte a été extrait, c'est un PDF textuel
        if text.strip():
            return {
                "text": text.strip(),
                "extraction_method": "text_extraction",
                "document_type": "pdf_text"
            }
        
        # Sinon, c'est probablement un PDF scanné, utiliser OCR si disponible
        if PDF2IMAGE_AVAILABLE and TESSERACT_AVAILABLE:
            return TextExtractor.extract_from_scanned_pdf(pdf_path)
        else:
            return {
                "error": "PDF scanné détecté mais les bibliothèques nécessaires pour l'OCR ne sont pas disponibles.",
                "required_packages": ["pdf2image", "pytesseract"]
            }
    
    @staticmethod
    def extract_from_scanned_pdf(pdf_path):
        """
        Extrait le texte d'un PDF scanné en utilisant OCR
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            
        Returns:
            dict: Dictionnaire contenant le texte extrait et des métadonnées
        """
        try:
            # Convertir le PDF en images
            with tempfile.TemporaryDirectory() as temp_dir:
                images = convert_from_path(pdf_path, output_folder=temp_dir)
                
                full_text = ""
                for i, image in enumerate(images):
                    # Appliquer OCR directement sur l'image PIL
                    text = pytesseract.image_to_string(image, lang='fra+eng')
                    full_text += text + "\n"
                
                return {
                    "text": full_text.strip(),
                    "extraction_method": "ocr",
                    "document_type": "pdf_scanned",
                    "page_count": len(images)
                }
        except Exception as e:
            return {"error": f"Erreur lors de l'extraction OCR: {str(e)}"}
    
    @staticmethod
    def extract_from_image(image_path):
        """
        Extrait le texte d'une image en utilisant OCR
        
        Args:
            image_path: Chemin vers le fichier image
            
        Returns:
            dict: Dictionnaire contenant le texte extrait et des métadonnées
        """
        if not TESSERACT_AVAILABLE:
            return {"error": "pytesseract n'est pas installé. Impossible d'extraire le texte de l'image."}
        
        try:
            # Charger l'image avec PIL
            image = Image.open(image_path)
            
            # Appliquer OCR
            text = pytesseract.image_to_string(image, lang='fra+eng')
            
            return {
                "text": text.strip(),
                "extraction_method": "ocr",
                "document_type": "image"
            }
        except Exception as e:
            return {"error": f"Erreur lors de l'extraction OCR: {str(e)}"}