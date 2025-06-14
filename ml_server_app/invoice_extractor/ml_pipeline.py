import os
import cv2
import numpy as np
import pytesseract
from PIL import Image
import pdf2image
import spacy
import re
from datetime import datetime, date
import tensorflow as tf
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InvoiceExtractionPipeline:
    def __init__(self):
        try:
            self.nlp = spacy.load("fr_core_news_md")
            logger.info("Modèle spaCy fr_core_news_md chargé")
        except:
            try:
                self.nlp = spacy.load("fr_core_news_sm")
                logger.info("Modèle spaCy fr_core_news_sm chargé")
            except Exception as e:
                logger.error(f"Erreur chargement spaCy: {str(e)}")
                raise
        
        self.tesseract_cmd = '/usr/local/bin/tesseract'
        if os.path.exists(self.tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        
        self.poppler_path = '/usr/local/bin'
        if not os.path.exists(self.poppler_path):
            self.poppler_path = None
    
    def process(self, file_path):
        try:
            logger.info(f"Traitement: {file_path}")
            _, ext = os.path.splitext(file_path)
            
            if ext.lower() == '.pdf':
                try:
                    if self.poppler_path and os.path.exists(self.poppler_path):
                        images = pdf2image.convert_from_path(file_path, dpi=300, poppler_path=self.poppler_path)
                    else:
                        images = pdf2image.convert_from_path(file_path, dpi=300)
                    logger.info(f"PDF converti: {len(images)} pages")
                except Exception as e:
                    logger.error(f"Erreur conversion PDF: {str(e)}")
                    return {"error": f"Erreur conversion PDF: {str(e)}"}
            else:
                img = cv2.imread(file_path)
                if img is None:
                    return {"error": f"Impossible de lire: {file_path}"}
                images = [img]
            
            processed_images = [self._preprocess_image(img) for img in images]
            
            text_content = ""
            for img in processed_images:
                text_content += pytesseract.image_to_string(img, lang='fra') + "\n"
            
            extracted_data = self._extract_information(text_content)
            extracted_data['document_type'] = self._classify_document(text_content, extracted_data)
            
            required_fields = ['invoice_number', 'invoice_date', 'total_amount', 'vendor_name']
            found_fields = sum(1 for field in required_fields if field in extracted_data and extracted_data[field])
            extracted_data['confidence_score'] = found_fields / len(required_fields)
            
            logger.info(f"Extraction terminée - Score: {extracted_data['confidence_score']:.2f}")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Erreur traitement: {str(e)}")
            return {"error": str(e)}
    
    def _preprocess_image(self, image):
        if isinstance(image, np.ndarray):
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        else:
            img_array = np.array(image)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
        
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        return binary
    
    def _extract_information(self, text):
        result = {}
        doc = self.nlp(text)
        
        # Numéro de facture - Patterns améliorés basés sur les exemples
        invoice_patterns = [
            r'(?i)facture\s*n[°o]?\s*[:\s]*([A-Z0-9][\w\d\-\.\/]{3,25})',
            r'(?i)facture\s*[:\s]*n[°o]?\s*([A-Z0-9][\w\d\-\.\/]{3,25})',
            r'(?i)n[°o]\s*(?:de\s*)?facture\s*[:\s]*([A-Z0-9][\w\d\-\.\/]{3,25})',
            r'(?i)(?:invoice|fact\.?)\s*n[°o]?\s*[:\s]*([A-Z0-9][\w\d\-\.\/]{3,25})',
            r'(?i)numéro\s*de\s*facturation\s*[:\s]*([A-Z0-9][\w\d\-\.\/]{3,25})',
            r'(?i)ID\s*DE\s*FACTURE\s*[:\s]*([A-Z0-9\-]{8,})',
            r'(?i)reçu\s*[:\s]*([A-Z0-9][\w\d\-\.\/]{3,25})'
        ]
        
        for pattern in invoice_patterns:
            matches = re.findall(pattern, text)
            if matches:
                invoice_number = matches[0].strip()
                if not re.match(r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}', invoice_number):
                    result['invoice_number'] = invoice_number
                    break
        
        # Date de facture - Patterns étendus
        date_patterns = [
            r'(?i)facture\s*n[°o]?\s*[A-Z0-9\-\.\/]+\s*du\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'(?i)facture\s*du\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'(?i)date\s*[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'(?i)date\s*de\s*facturation\s*[:\s]*(\d{1,2}\s*[a-zéèû]+\s*\d{4})',
            r'(?i)(\d{1,2}\s*(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s*\d{4})',
            r'(?i)émis\s*le\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'(?i)(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})',
            r'(?i)(\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                result['invoice_date'] = matches[0].strip()
                break
        
        # Date d'échéance
        due_date_patterns = [
            r'(?i)date\s*limite\s*de\s*paiement\s*[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'(?i)échéance\s*[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'(?i)date\s*d[\'"]échéance\s*[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'(?i)payer\s*avant\s*le\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})'
        ]
        
        for pattern in due_date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                result['due_date'] = matches[0].strip()
                break
        
        # Montant total - Patterns améliorés
        amount_patterns = [
            r'(?i)somme\s*à\s*payer\s*(?:ttc)?\s*[:\s]*(\d+[.,]\d{2})\s*€?',
            r'(?i)total\s*(?:ttc|à\s*payer)?\s*[:\s]*(\d+[.,]\d{2})\s*€?',
            r'(?i)montant\s*(?:total|dû|d[ûu])\s*(?:ttc)?\s*[:\s]*(\d+[.,]\d{2})\s*€?',
            r'(?i)total\s*général\s*[:\s]*(\d+[.,]\d{2})\s*€?',
            r'(?i)net\s*à\s*payer\s*[:\s]*(\d+[.,]\d{2})\s*€?',
            r'(?i)reste\s*à\s*payer\s*[:\s]*(\d+[.,]\d{2})\s*€?',
            r'(?i)prix\s*à\s*payer\s*[:\s]*(\d+[.,]\d{2})\s*€?',
            r'(?i)total\s*\([^)]*\)\s*[:\s]*(\d+[.,]\d{2})\s*€?'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    amount_str = matches[0].replace(',', '.')
                    result['total_amount'] = float(amount_str)
                    break
                except:
                    continue
        
        # Montant HT
        ht_patterns = [
            r'(?i)total\s*ht\s*[:\s]*(\d+[.,]\d{2})\s*€?',
            r'(?i)montant\s*ht\s*[:\s]*(\d+[.,]\d{2})\s*€?',
            r'(?i)total\s*hors\s*taxe\s*[:\s]*(\d+[.,]\d{2})\s*€?',
            r'(?i)sous[-\s]total\s*[:\s]*(\d+[.,]\d{2})\s*€?'
        ]
        
        for pattern in ht_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    result['net_amount'] = float(matches[0].replace(',', '.'))
                    break
                except:
                    continue
        
        # TVA
        tax_patterns = [
            r'(?i)tva\s*\[(\d{1,2}[.,]?\d*)\s*%\]\s*(\d+[.,]\d{2})\s*€?',
            r'(?i)montant\s*tva\s*\((\d{1,2}[.,]?\d*)\s*%\)\s*(\d+[.,]\d{2})\s*€?',
            r'(?i)tva\s*(\d{1,2}[.,]?\d*)\s*%\s*[:\s]*(\d+[.,]\d{2})\s*€?',
            r'(?i)total\s*tva\s*(\d{1,2}[.,]?\d*)\s*%\s*[:\s]*(\d+[.,]\d{2})\s*€?'
        ]
        
        for pattern in tax_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    if len(matches[0]) == 2:
                        result['tax_rate'] = float(matches[0][0].replace(',', '.'))
                        result['tax_amount'] = float(matches[0][1].replace(',', '.'))
                    else:
                        result['tax_amount'] = float(matches[0].replace(',', '.'))
                    break
                except:
                    continue
        
        # Nom du fournisseur - Logique améliorée
        vendor_patterns = [
            r'(?i)émise?\s*par\s*[:\s]*([A-Z][A-Za-z0-9\s\-\.]{2,50})',
            r'(?i)facturé\s*par\s*[:\s]*([A-Z][A-Za-z0-9\s\-\.]{2,50})',
            r'(?i)vendeur\s*[:\s]*([A-Z][A-Za-z0-9\s\-\.]{2,50})',
            r'(?:^|\n)([A-Z][A-Z\s&\-\.]{3,50})\n',
            r'(?:^|\n)([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){1,3})\n'
        ]
        
        # Extraction par NER d'abord
        org_entities = [ent.text.strip() for ent in doc.ents if ent.label_ == "ORG" and 3 <= len(ent.text.strip()) <= 50]
        
        # Filtrer les organisations valides
        valid_orgs = []
        for org in org_entities:
            org_clean = org.strip()
            if (len(org_clean) >= 3 and 
                not re.match(r'^\d+[.,]\d{2}$', org_clean) and 
                not re.match(r'^\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}$', org_clean) and
                not org_clean.lower() in ['tva', 'ttc', 'ht', 'euro', 'france']):
                valid_orgs.append(org_clean)
        
        if valid_orgs:
            result['vendor_name'] = valid_orgs[0]
        else:
            # Fallback sur les patterns regex
            for pattern in vendor_patterns:
                matches = re.findall(pattern, text, re.MULTILINE)
                if matches:
                    vendor_name = matches[0].strip()
                    if (len(vendor_name) >= 3 and 
                        not re.match(r'^\d+[.,]\d{2}$', vendor_name) and
                        not vendor_name.lower() in ['facture', 'total', 'montant']):
                        result['vendor_name'] = vendor_name
                        break
        
        # Adresse du fournisseur
        address_patterns = [
            r'(?i)(\d{1,4}[,\s]+(?:rue|avenue|boulevard|impasse|allée|place|voie)[,\s]+[^,\n]{5,50})',
            r'(?i)(\d{5}[,\s]+[A-Z][A-Za-z\-\s]{2,50})',
            r'(?i)((?:\d{1,4}[,\s]+)?[A-Za-z\-\s]{5,50}[,\s]+\d{5}[,\s]+[A-Z][A-Za-z\-\s]{2,50})'
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text)
            if matches:
                result['vendor_address'] = matches[0].strip()
                break
        
        # SIRET/SIREN
        siret_patterns = [
            r'(?i)siret[:\s]*(\d{14})',
            r'(?i)siren[:\s]*(\d{9})',
            r'(?i)rcs[^0-9]*(\d{9})',
            r'(?i)(\d{3}\s?\d{3}\s?\d{3}\s?\d{5})'
        ]
        
        for pattern in siret_patterns:
            matches = re.findall(pattern, text)
            if matches:
                number = re.sub(r'\s', '', matches[0])
                if len(number) == 14:
                    result['siret'] = number
                elif len(number) == 9:
                    result['siren'] = number
                break
        
        # Numéro de TVA intracommunautaire
        vat_patterns = [
            r'(?i)n[°o]?\s*tva\s*intracommunautaire\s*[:\s]*([A-Z]{2}[\s\-]*\d{2,14})',
            r'(?i)tva\s*id\s*[:\s]*([A-Z]{2}\d{2,14})',
            r'(?i)vat\s*id\s*[:\s]*([A-Z]{2}\d{2,14})',
            r'(?i)([A-Z]{2}\d{11})',
            r'(?i)fr\s*(\d{11})'
        ]
        
        for pattern in vat_patterns:
            matches = re.findall(pattern, text)
            if matches:
                vat_number = re.sub(r'[\s\-\.]', '', matches[0])
                if pattern.endswith(r'fr\s*(\d{11})'):
                    vat_number = 'FR' + vat_number
                result['vat_number'] = vat_number
                break
        
        # Client/Destinataire
        client_patterns = [
            r"(?i)date\s*d['’]échéance\s*[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
            r"(?i)adresse\s*de\s*facturation[:\s]*\n([A-Z][A-Za-z\s\-\.]{2,50})"
        ]
        
        for pattern in client_patterns:
            matches = re.findall(pattern, text)
            if matches:
                result['client_name'] = matches[0].strip()
                break
        
        return result
    
    def _classify_document(self, text, extracted_data):
        text_lower = text.lower()
        
        # Compteurs pour différents types de documents
        invoice_keywords = ['facture', 'invoice', 'facturation', 'avis d\'échéance']
        quote_keywords = ['devis', 'quotation', 'estimation', 'proposition commerciale']
        receipt_keywords = ['reçu', 'receipt', 'ticket', 'justificatif']
        
        invoice_count = sum(text_lower.count(keyword) for keyword in invoice_keywords)
        quote_count = sum(text_lower.count(keyword) for keyword in quote_keywords)
        receipt_count = sum(text_lower.count(keyword) for keyword in receipt_keywords)
        
        # Classification basée sur les mots-clés et les données extraites
        if invoice_count > max(quote_count, receipt_count):
            return 'invoice'
        elif quote_count > max(invoice_count, receipt_count):
            return 'quote'
        elif receipt_count > max(invoice_count, quote_count):
            return 'receipt'
        else:
            # Classification basée sur la structure des données
            has_invoice_structure = (
                'invoice_number' in extracted_data and 
                'total_amount' in extracted_data and 
                'vendor_name' in extracted_data
            )
            
            if has_invoice_structure:
                return 'invoice'
            elif 'total_amount' in extracted_data:
                return 'receipt'
            else:
                return 'unknown'