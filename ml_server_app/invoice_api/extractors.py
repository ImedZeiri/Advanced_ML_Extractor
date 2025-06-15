import os
import tempfile
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
        
        if file_ext == '.pdf':
            return TextExtractor.extract_from_pdf(file_path)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            return TextExtractor.extract_from_image(file_path)
        else:
            return {"error": "Format de fichier non pris en charge"}
    
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