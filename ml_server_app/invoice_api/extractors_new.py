import os
import tempfile
import re
from PIL import Image
import json

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
    @staticmethod
    def clean_text(text):
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
        data = {
            "numeroFacture": None,
            "numeroCommande": None,
            "numeroContrat": None,
            "datePiece": None,
            "dateCommande": None,
            "dateLivraison": None,
            "client": {
                "societe": None,
                "code": None,
                "tva": None,
                "siret": None,
                "ville": None,
                "pays": None
            },
            "totalTTC": None,
            "totalHT": None,
            "totalTVA": None,
            "articles": []
        }
        
        # Extraire le numéro de facture
        invoice_patterns = [
            r'(?i)(?:facture|invoice|n°|numéro|ref)[\s:]*([A-Z0-9-]{5,})',
            r'(?i)(?:facture|invoice)[^\n]*?(?:n°|numéro|ref)[^\n]*?([A-Z0-9-]{5,})'
        ]
        
        for pattern in invoice_patterns:
            invoice_match = re.search(pattern, text)
            if invoice_match:
                data["numeroFacture"] = invoice_match.group(1).strip()
                break
        
        # Extraire le numéro de commande
        order_patterns = [
            r'(?i)(?:commande|order|n°\s*commande|numéro\s*commande)[\s:]*([A-Z0-9-]{3,})',
            r'(?i)(?:bon\s*de\s*commande)[^\n]*?(?:n°|numéro)[^\n]*?([A-Z0-9-]{3,})'
        ]
        
        for pattern in order_patterns:
            order_match = re.search(pattern, text)
            if order_match:
                data["numeroCommande"] = order_match.group(1).strip()
                break
        
        # Extraire le numéro de contrat
        contract_patterns = [
            r'(?i)(?:contrat|contract|n°\s*contrat|numéro\s*contrat)[\s:]*([A-Z0-9-]{3,})',
        ]
        
        for pattern in contract_patterns:
            contract_match = re.search(pattern, text)
            if contract_match:
                data["numeroContrat"] = contract_match.group(1).strip()
                break
        
        # Extraire les dates
        date_patterns = {
            "datePiece": [
                r'(?i)(?:date|émission|facturé le|date\s*facture)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?i)(?:date|émission)[^\n]*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            "dateCommande": [
                r'(?i)(?:date\s*commande|date\s*de\s*commande)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ],
            "dateLivraison": [
                r'(?i)(?:date\s*livraison|date\s*de\s*livraison|livré\s*le)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ]
        }
        
        # Si aucune date spécifique n'est trouvée, utiliser la première date du document
        general_date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        
        for date_field, patterns in date_patterns.items():
            for pattern in patterns:
                date_match = re.search(pattern, text)
                if date_match:
                    data[date_field] = date_match.group(1).strip()
                    break
        
        # Si datePiece est toujours null, chercher une date générique
        if data["datePiece"] is None:
            date_match = re.search(general_date_pattern, text)
            if date_match:
                data["datePiece"] = date_match.group(1).strip()
        
        # Extraire les informations du client
        client_patterns = {
            "societe": [
                r'(?i)(?:client|customer|acheteur|destinataire)[\s:]*([A-Za-z0-9\s]{3,50})',
                r'(?i)(?:facturer\s*à|facturé\s*à)[\s:]*([A-Za-z0-9\s]{3,50})'
            ],
            "code": [
                r'(?i)(?:code\s*client|customer\s*code|référence\s*client)[\s:]*([A-Za-z0-9-]{2,20})'
            ],
            "tva": [
                r'(?i)(?:TVA\s*client|TVA\s*intra|n°\s*TVA)[\s:]*([A-Z0-9]{2,14})'
            ],
            "siret": [
                r'(?i)(?:SIRET\s*client)[\s:]*(\d{14})'
            ],
            "ville": [
                r'(?i)(?:ville|city)[\s:]*([A-Za-z\s-]{2,30})',
                r'(?i)\b([A-Z][A-Za-z\s-]{2,25})\s+\d{5}\b'
            ],
            "pays": [
                r'(?i)(?:pays|country)[\s:]*([A-Za-z\s-]{3,20})'
            ]
        }
        
        for field, patterns in client_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    data["client"][field] = match.group(1).strip()
                    break
        
        # Extraire les montants
        amount_patterns = {
            "totalTTC": [
                r'(?i)(?:total\s*ttc|montant\s*ttc|net\s*à\s*payer|total\s*à\s*payer)[\s:]*(\d+[,.]\d{2})',
                r'(?i)(?:ttc)[^\n]*?(\d+[,.]\d{2})\s*(?:€|EUR|EURO|EUROS)?'
            ],
            "totalHT": [
                r'(?i)(?:total\s*ht|montant\s*ht|prix\s*ht)[\s:]*(\d+[,.]\d{2})',
                r'(?i)(?:ht)[^\n]*?(\d+[,.]\d{2})\s*(?:€|EUR|EURO|EUROS)?'
            ],
            "totalTVA": [
                r'(?i)(?:total\s*tva|montant\s*tva|tva)[\s:]*(\d+[,.]\d{2})',
                r'(?i)(?:tva)[^\n]*?(\d+[,.]\d{2})\s*(?:€|EUR|EURO|EUROS)?'
            ]
        }
        
        for amount_field, patterns in amount_patterns.items():
            for pattern in patterns:
                amount_match = re.search(pattern, text)
                if amount_match:
                    data[amount_field] = amount_match.group(1).replace(',', '.')
                    break
        
        # Extraire les articles/lignes de produits
        # Recherche de tableaux ou de listes d'articles
        product_lines_pattern = r'(?i)(?:Désignation|Article|Produit|Description).*?(?:Quantité|Qté|Qte).*?(?:Prix|Montant|Total)'
        if re.search(product_lines_pattern, text):
            # Présence probable d'un tableau de produits
            lines = text.split('\n')
            product_section = False
            product_lines = []
            
            for line in lines:
                if re.search(product_lines_pattern, line):
                    product_section = True
                    continue
                
                if product_section and re.search(r'(?i)(?:Total|Sous-total)', line):
                    product_section = False
                    
                if product_section and re.search(r'\d+[,.]\d{2}', line):
                    # Ligne contenant probablement un prix
                    product_lines.append(line.strip())
            
            # Essayer d'extraire des informations structurées pour chaque ligne de produit
            for line in product_lines:
                article = {
                    "nom": line,  # Par défaut, utiliser la ligne complète comme nom
                    "quantite": None,
                    "prixHT": None,
                    "remise": None,
                    "totalHT": None,
                    "totalTTC": None
                }
                
                # Essayer d'extraire la quantité
                qty_match = re.search(r'\b(\d+(?:[,.]\d+)?)\s*(?:x|pcs|u|unités?)\b', line)
                if qty_match:
                    article["quantite"] = qty_match.group(1).replace(',', '.')
                
                # Essayer d'extraire le prix unitaire HT
                price_match = re.search(r'\b(\d+[,.]\d{2})\s*(?:€|EUR)?\s*(?:HT|H\.T\.)\b', line)
                if price_match:
                    article["prixHT"] = price_match.group(1).replace(',', '.')
                
                # Essayer d'extraire le total HT
                total_ht_match = re.search(r'\b(\d+[,.]\d{2})\s*(?:€|EUR)?\s*(?:HT|H\.T\.)\b', line)
                if total_ht_match and article["prixHT"] is None:  # Si pas déjà trouvé comme prix unitaire
                    article["totalHT"] = total_ht_match.group(1).replace(',', '.')
                
                # Ajouter l'article à la liste
                data["articles"].append(article)
        
        return data
    
    @staticmethod
    def process_extracted_text(extraction_result):
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