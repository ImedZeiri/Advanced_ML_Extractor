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
            "invoice_number": None,
            "date": None,
            "total_amount": None,
            "vendor": None,
            "client": None,
            "payment_info": {},
            "tax_info": {},
            "items": [],
            "detected_fields": {},
            "categorized_fields": {
                "vendor_info": {},
                "client_info": {},
                "payment_details": {},
                "tax_details": {},
                "product_details": {},
                "dates": {},
                "totals": {},
                "other": {}
            }
        }
        
        # Format JSON demandé
        json_output = {
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
        
        # Dictionnaires de mots-clés pour la catégorisation
        field_categories = {
            "vendor_info": [
                "fournisseur", "vendeur", "émetteur", "société", "entreprise", "siret", "siren", 
                "rcs", "capital", "adresse", "tel", "téléphone", "email", "courriel", "site", 
                "web", "http", "www", "magasin", "boutique"
            ],
            "client_info": [
                "client", "acheteur", "destinataire", "livraison", "facturation", "adresse de",
                "adresse du", "compte client", "référence client"
            ],
            "payment_details": [
                "paiement", "règlement", "échéance", "date limite", "iban", "bic", "swift", "virement",
                "chèque", "carte", "bancaire", "payé", "réglé", "mode de", "conditions", "délai"
            ],
            "tax_details": [
                "tva", "taxe", "tax", "vat", "taux", "intracommunautaire", "exonéré", "n° tva", 
                "numéro tva", "id tva"
            ],
            "product_details": [
                "produit", "article", "référence", "ref", "désignation", "description", "quantité", 
                "qté", "prix", "unitaire", "pu", "remise", "sous-total", "sous total"
            ],
            "dates": [
                "date", "émission", "facture", "livraison", "échéance", "paiement", "commande"
            ],
            "totals": [
                "total", "ht", "ttc", "tva", "net à payer", "montant", "somme", "sous-total", 
                "remise", "frais", "port", "livraison", "acompte"
            ]
        }
        
        # Extraire le numéro de facture
        invoice_patterns = [
            r'(?i)(?:facture|invoice|n°|numéro|ref)[\s:]*([A-Z0-9-]{5,})',
            r'(?i)(?:facture|invoice)[^\n]*?(?:n°|numéro|ref)[^\n]*?([A-Z0-9-]{5,})'
        ]
        
        for pattern in invoice_patterns:
            invoice_match = re.search(pattern, text)
            if invoice_match:
                data["invoice_number"] = invoice_match.group(1).strip()
                json_output["numeroFacture"] = invoice_match.group(1).strip()
                break
                
        # Extraire le numéro de commande
        order_patterns = [
            r'(?i)(?:commande|order|n°\s*commande|numéro\s*commande|référence\s*commande)[\s:]*([A-Z0-9-]{3,})',
            r'(?i)(?:bon\s*de\s*commande)[\s:]*([A-Z0-9-]{3,})'
        ]
        
        for pattern in order_patterns:
            order_match = re.search(pattern, text)
            if order_match:
                json_output["numeroCommande"] = order_match.group(1).strip()
                break
                
        # Extraire le numéro de contrat
        contract_patterns = [
            r'(?i)(?:contrat|contract|n°\s*contrat|numéro\s*contrat)[\s:]*([A-Z0-9-]{3,})'
        ]
        
        for pattern in contract_patterns:
            contract_match = re.search(pattern, text)
            if contract_match:
                json_output["numeroContrat"] = contract_match.group(1).strip()
                break
        
        # Extraire les dates (avec différents formats)
        date_patterns = [
            r'(?i)(?:date|émission|facturé le)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{2,4})'
        ]
        
        # Date de la pièce (facture)
        for pattern in date_patterns:
            date_match = re.search(pattern, text)
            if date_match:
                data["date"] = date_match.group(1).strip()
                json_output["datePiece"] = date_match.group(1).strip()
                break
                
        # Date de commande
        order_date_patterns = [
            r'(?i)(?:date\s*(?:de\s*)?commande|order\s*date)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in order_date_patterns:
            order_date_match = re.search(pattern, text)
            if order_date_match:
                json_output["dateCommande"] = order_date_match.group(1).strip()
                break
                
        # Date de livraison
        delivery_date_patterns = [
            r'(?i)(?:date\s*(?:de\s*)?livraison|delivery\s*date|livré\s*le)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in delivery_date_patterns:
            delivery_date_match = re.search(pattern, text)
            if delivery_date_match:
                json_output["dateLivraison"] = delivery_date_match.group(1).strip()
                break
        
        # Extraire le montant total TTC
        total_ttc_patterns = [
            r'(?i)(?:total\s+ttc|montant\s+ttc|net\s+à\s+payer|total\s+à\s+payer)[\s:]*(\d+[,.]\d{2})',
            r'(?i)(?:ttc|t\.t\.c\.).*?(\d+[,.]\d{2})\s*(?:€|EUR|EURO|EUROS)?',
            r'(?i)(?:à\s+payer)[\s:]*(\d+[,.]\d{2})'
        ]
        
        for pattern in total_ttc_patterns:
            amount_match = re.search(pattern, text)
            if amount_match:
                amount = amount_match.group(1).replace(',', '.')
                data["total_amount"] = amount
                json_output["totalTTC"] = amount
                break
                
        # Extraire le montant total HT
        total_ht_patterns = [
            r'(?i)(?:total\s+ht|montant\s+ht|prix\s+ht)[\s:]*(\d+[,.]\d{2})',
            r'(?i)(?:ht|h\.t\.).*?(\d+[,.]\d{2})\s*(?:€|EUR|EURO|EUROS)?'
        ]
        
        for pattern in total_ht_patterns:
            ht_match = re.search(pattern, text)
            if ht_match:
                json_output["totalHT"] = ht_match.group(1).replace(',', '.')
                break
                
        # Extraire le montant total TVA
        total_tva_patterns = [
            r'(?i)(?:total\s+tva|montant\s+tva|tva)[\s:]*(\d+[,.]\d{2})',
            r'(?i)(?:tva|t\.v\.a\.).*?(\d+[,.]\d{2})\s*(?:€|EUR|EURO|EUROS)?'
        ]
        
        for pattern in total_tva_patterns:
            tva_match = re.search(pattern, text)
            if tva_match:
                json_output["totalTVA"] = tva_match.group(1).replace(',', '.')
                break
        
        # Extraire les informations du client
        client_patterns = {
            "societe": r'(?i)(?:client|customer|acheteur|destinataire)[\s:]*([A-Za-z0-9\s\-\'\.&]{3,50})',
            "code": r'(?i)(?:code\s*client|customer\s*code|référence\s*client)[\s:]*([A-Za-z0-9\-]{2,20})',
            "tva": r'(?i)(?:tva\s*client|tva\s*intra|n°\s*tva)[\s:]*([A-Za-z0-9]{2,14})',
            "siret": r'(?i)(?:siret\s*client|siret)[\s:]*(\d{14})',
            "ville": r'(?i)(?:ville|city|localité)[\s:]*([A-Za-z\s\-\']{2,30})',
            "pays": r'(?i)(?:pays|country)[\s:]*([A-Za-z\s\-\']{2,30})'
        }
        
        for key, pattern in client_patterns.items():
            match = re.search(pattern, text)
            if match:
                json_output["client"][key] = match.group(1).strip()
                
        # Extraire les informations du fournisseur (pour le modèle de données existant)
        vendor_patterns = {
            "siret": r'(?i)(?:SIRET)[\s:]*(\d{14})',
            "siren": r'(?i)(?:SIREN)[\s:]*(\d{9})',
            "website": r'(?i)(?:www\.[\w-]+\.[\w]{2,}|https?://[\w-]+\.[\w]{2,}[\w/\-\.]*)',
            "email": r'[\w\.-]+@[\w\.-]+\.\w+',
            "phone": r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}'
        }
        
        for key, pattern in vendor_patterns.items():
            match = re.search(pattern, text)
            if match:
                if key == "website" or key == "email" or key == "phone":
                    data["categorized_fields"]["vendor_info"][key] = match.group(0)
                else:
                    data["categorized_fields"]["vendor_info"][key] = match.group(1)
        
        # Extraire les informations de TVA
        vat_patterns = {
            "tva_number": r'(?i)(?:TVA|VAT|n°\s*TVA|numéro\s*TVA)[\s:]*([A-Z0-9]{2,14})',
            "tva_rate": r'(?i)(?:TVA|VAT|Taux)[\s:]*(\d{1,2}[,.]\d{1,2}\s*%|\d{1,2}\s*%)'
        }
        
        for key, pattern in vat_patterns.items():
            match = re.search(pattern, text)
            if match:
                data["categorized_fields"]["tax_details"][key] = match.group(1)
        
        # Extraire les lignes de produits/services
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
            
            if product_lines:
                data["items"] = product_lines
                
                # Essayer d'extraire les détails des articles pour le format JSON demandé
                for line in product_lines:
                    # Modèle simplifié pour extraire les informations d'un article
                    article = {
                        "nom": None,
                        "quantite": None,
                        "prixHT": None,
                        "remise": None,
                        "totalHT": None,
                        "totalTTC": None
                    }
                    
                    # Extraction du nom de l'article (première partie de la ligne avant les chiffres)
                    nom_match = re.match(r'^(.*?)(?:\d+[,.]\d{2}|\d+\s*(?:x|pcs|u|unité))', line)
                    if nom_match:
                        article["nom"] = nom_match.group(1).strip()
                    
                    # Extraction de la quantité
                    qty_match = re.search(r'(\d+(?:[,.]\d+)?)\s*(?:x|pcs|u|unité)', line)
                    if qty_match:
                        article["quantite"] = qty_match.group(1).replace(',', '.')
                    
                    # Extraction du prix HT
                    prix_ht_match = re.search(r'(?:prix|p\.u\.|pu|unitaire)[\s:]*(\d+[,.]\d{2})', line, re.IGNORECASE)
                    if prix_ht_match:
                        article["prixHT"] = prix_ht_match.group(1).replace(',', '.')
                    
                    # Extraction de la remise
                    remise_match = re.search(r'(?:remise|discount)[\s:]*(\d+[,.]\d{2}|\d+\s*%)', line, re.IGNORECASE)
                    if remise_match:
                        article["remise"] = remise_match.group(1).replace(',', '.')
                    
                    # Extraction du total HT
                    total_ht_match = re.search(r'(?:total\s*ht|ht)[\s:]*(\d+[,.]\d{2})', line, re.IGNORECASE)
                    if total_ht_match:
                        article["totalHT"] = total_ht_match.group(1).replace(',', '.')
                    
                    # Extraction du total TTC
                    total_ttc_match = re.search(r'(?:total\s*ttc|ttc)[\s:]*(\d+[,.]\d{2})', line, re.IGNORECASE)
                    if total_ttc_match:
                        article["totalTTC"] = total_ttc_match.group(1).replace(',', '.')
                    
                    # Si on n'a pas trouvé de nom mais qu'on a d'autres informations, utiliser la ligne entière comme nom
                    if not article["nom"] and (article["quantite"] or article["prixHT"] or article["totalHT"]):
                        article["nom"] = line.strip()
                    
                    # Ajouter l'article seulement s'il a au moins un nom
                    if article["nom"]:
                        json_output["articles"].append(article)
        
        # Détecter automatiquement les paires clé-valeur
        key_value_patterns = [
            r'([A-Za-z0-9\s\-\']{3,30})\s*[:=]\s*([A-Za-z0-9\s\-\.,€\$£&@\'\/]{1,50})',  # Clé: Valeur ou Clé = Valeur
            r'([A-Za-z0-9\s\-\']{3,30})\s*[:|]\s*([A-Za-z0-9\s\-\.,€\$£&@\'\/]{1,50})',  # Clé: Valeur ou Clé | Valeur
            r'([A-Za-z0-9\s\-\']{3,30})\s{2,}([A-Za-z0-9\s\-\.,€\$£&@\'\/]{1,50})'       # Clé suivie de plusieurs espaces puis Valeur
        ]
        
        for pattern in key_value_patterns:
            for match in re.finditer(pattern, text):
                key = match.group(1).strip()
                value = match.group(2).strip()
                
                # Ignorer les clés trop courtes ou les valeurs vides
                if len(key) < 3 or not value:
                    continue
                    
                # Ignorer les clés qui sont des mots communs
                common_words = ['le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'pour', 'par', 'avec', 'dans']
                if key.lower() in common_words:
                    continue
                
                # Nettoyer la clé et la valeur
                key = key.strip().capitalize()
                value = value.strip()
                
                # Ajouter au dictionnaire des champs détectés
                data["detected_fields"][key] = value
                
                # Catégoriser le champ
                categorized = False
                for category, keywords in field_categories.items():
                    for keyword in keywords:
                        if keyword.lower() in key.lower():
                            data["categorized_fields"][category][key] = value
                            categorized = True
                            break
                    if categorized:
                        break
                
                # Si non catégorisé, mettre dans "other"
                if not categorized:
                    data["categorized_fields"]["other"][key] = value
        
        # Ajouter le format JSON au résultat
        data["json_output"] = json_output
        
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