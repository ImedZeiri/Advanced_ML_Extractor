import os
import json
import torch
import numpy as np
from PIL import Image
from transformers import LayoutLMv3Processor, LayoutLMv3ForSequenceClassification, LayoutLMv3ForTokenClassification
from transformers import AdamW
from torch.utils.data import Dataset, DataLoader
import pytesseract
from pdf2image import convert_from_path
import tempfile
import logging
from django.conf import settings
from .models import Invoice, InvoiceAnnotation

logger = logging.getLogger(__name__)

class InvoiceDataset(Dataset):
    """Dataset pour les factures annotées"""
    
    def __init__(self, annotations, processor, max_length=512):
        self.annotations = annotations
        self.processor = processor
        self.max_length = max_length
        
    def __len__(self):
        return len(self.annotations)
    
    def __getitem__(self, idx):
        annotation = self.annotations[idx]
        
        # Charger l'image
        image_path = os.path.join(settings.MEDIA_ROOT, annotation['image_path'])
        
        # Si c'est un PDF, convertir en image
        if image_path.lower().endswith('.pdf'):
            try:
                # Utiliser une copie temporaire du fichier pour éviter les problèmes d'accès
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_pdf = os.path.join(temp_dir, "temp.pdf")
                    with open(image_path, 'rb') as src_file, open(temp_pdf, 'wb') as dst_file:
                        dst_file.write(src_file.read())
                    
                    # Convertir le PDF en image sans sauvegarder les images intermédiaires
                    images = convert_from_path(temp_pdf, output_folder=None)
                    # Convertir l'image PIL en mémoire pour éviter les problèmes de fichiers
                    image = images[0].copy()
            except Exception as e:
                # En cas d'erreur, utiliser une image vide
                logger.error(f"Erreur lors de la conversion du PDF: {str(e)}")
                image = Image.new('RGB', (100, 100), color='white')
        else:
            image = Image.open(image_path).convert("RGB")
        
        # Extraire le texte avec OCR si nécessaire
        if 'ocr_text' in annotation and annotation['ocr_text']:
            words = annotation['ocr_text'].split()
            boxes = annotation.get('boxes', [])
            if not boxes:
                # Générer des boîtes factices si non disponibles
                boxes = [[0, 0, 100, 100]] * len(words)
        else:
            # Faire l'OCR
            ocr_result = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang='fra+eng')
            words = [word for word in ocr_result['text'] if word.strip()]
            boxes = []
            for i in range(len(ocr_result['text'])):
                if ocr_result['text'][i].strip():
                    x, y, w, h = ocr_result['left'][i], ocr_result['top'][i], ocr_result['width'][i], ocr_result['height'][i]
                    boxes.append([x, y, x + w, y + h])
        
        # Préparer les étiquettes pour chaque mot
        labels = []
        for word in words:
            # Logique pour attribuer des étiquettes en fonction des données annotées
            # Par exemple, vérifier si le mot correspond à un numéro de facture, une date, etc.
            # Pour simplifier, on utilise une étiquette générique ici
            labels.append(0)  # 0 = autre, 1 = numéro de facture, 2 = date, etc.
        
        # Encoder les entrées
        encoding = self.processor(
            image,
            text=words,
            boxes=boxes,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
            apply_ocr=False  # Désactiver l'OCR car nous fournissons déjà les mots et les boîtes
        )
        
        # Ajouter les étiquettes
        encoding["labels"] = torch.tensor(labels)
        
        # Supprimer la dimension batch
        for k, v in encoding.items():
            encoding[k] = v.squeeze()
            
        return encoding

class LayoutLMv3Extractor:
    """Classe pour l'extraction d'informations à partir de factures en utilisant LayoutLMv3"""
    
    def __init__(self):
        self.model_path = os.path.join(settings.BASE_DIR, 'invoice_api', 'models', 'layoutlmv3')
        self.processor = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.label_map = {
            0: "O",  # Autre
            1: "B-INVOICE_NUM",  # Début de numéro de facture
            2: "I-INVOICE_NUM",  # Suite de numéro de facture
            3: "B-DATE",  # Début de date
            4: "I-DATE",  # Suite de date
            5: "B-TOTAL",  # Début de montant total
            6: "I-TOTAL",  # Suite de montant total
            7: "B-COMPANY",  # Début de nom d'entreprise
            8: "I-COMPANY",  # Suite de nom d'entreprise
            # Ajouter d'autres étiquettes selon les besoins
        }
        self.load_model()
    
    def load_model(self):
        """Charge le modèle LayoutLMv3 et le processeur"""
        try:
            # Vérifier si un modèle personnalisé existe
            if os.path.exists(self.model_path):
                logger.info(f"Chargement du modèle personnalisé depuis {self.model_path}")
                self.processor = LayoutLMv3Processor.from_pretrained(self.model_path)
                self.model = LayoutLMv3ForTokenClassification.from_pretrained(self.model_path)
            else:
                # Utiliser le modèle pré-entraîné par défaut
                logger.info("Chargement du modèle pré-entraîné LayoutLMv3")
                self.processor = LayoutLMv3Processor.from_pretrained("microsoft/layoutlmv3-base")
                self.model = LayoutLMv3ForTokenClassification.from_pretrained(
                    "microsoft/layoutlmv3-base",
                    num_labels=len(self.label_map)
                )
                
                # Créer le répertoire pour sauvegarder le modèle
                os.makedirs(self.model_path, exist_ok=True)
                
            self.model.to(self.device)
            logger.info("Modèle LayoutLMv3 chargé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle LayoutLMv3: {str(e)}")
            self.processor = None
            self.model = None
    
    def extract_from_image(self, image_path):
        """Extrait les informations structurées à partir d'une image de facture"""
        if self.processor is None or self.model is None:
            logger.error("Le modèle LayoutLMv3 n'est pas chargé")
            return {"error": "Modèle non disponible"}
        
        try:
            # Charger l'image
            if image_path.lower().endswith('.pdf'):
                try:
                    # Utiliser une copie temporaire du fichier pour éviter les problèmes d'accès
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_pdf = os.path.join(temp_dir, "temp.pdf")
                        with open(image_path, 'rb') as src_file, open(temp_pdf, 'wb') as dst_file:
                            dst_file.write(src_file.read())
                        
                        # Convertir le PDF en image
                        images = convert_from_path(temp_pdf, output_folder=temp_dir)
                        # Convertir l'image PIL en mémoire pour éviter les problèmes de fichiers
                        image = images[0].copy()
                except Exception as e:
                    logger.error(f"Erreur lors de la conversion du PDF: {str(e)}")
                    # Fallback: retourner une erreur
                    return {"error": f"Erreur lors de la conversion du PDF: {str(e)}"}
            else:
                image = Image.open(image_path).convert("RGB")
            
            # Extraire le texte avec OCR
            ocr_result = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang='fra+eng')
            words = []
            boxes = []
            
            for i in range(len(ocr_result['text'])):
                if ocr_result['text'][i].strip():
                    words.append(ocr_result['text'][i])
                    x, y, w, h = ocr_result['left'][i], ocr_result['top'][i], ocr_result['width'][i], ocr_result['height'][i]
                    boxes.append([x, y, x + w, y + h])
            
            # Encoder les entrées
            encoding = self.processor(
                image,
                text=words,
                boxes=boxes,
                truncation=True,
                padding="max_length",
                max_length=512,
                return_tensors="pt",
                apply_ocr=False  # Désactiver l'OCR car nous fournissons déjà les mots et les boîtes
            )
            
            # Déplacer les tenseurs vers le device
            for k, v in encoding.items():
                encoding[k] = v.to(self.device)
            
            # Prédiction
            with torch.no_grad():
                outputs = self.model(**encoding)
                predictions = outputs.logits.argmax(-1).squeeze().tolist()
            
            # Traiter les prédictions
            results = self.process_predictions(words, boxes, predictions)
            
            # Calculer les scores de confiance
            confidence_scores = self.calculate_confidence_scores(outputs.logits.squeeze())
            
            # Ajouter les scores de confiance aux résultats
            results["confidence_scores"] = confidence_scores
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction avec LayoutLMv3: {str(e)}")
            return {"error": f"Erreur d'extraction: {str(e)}"}
    
    def process_predictions(self, words, boxes, predictions):
        """Traite les prédictions pour extraire les informations structurées"""
        # Initialiser le dictionnaire de résultats
        structured_data = {
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
        
        # Extraire les entités reconnues
        current_entity = None
        current_text = ""
        
        for i, (word, pred) in enumerate(zip(words, predictions)):
            label = self.label_map.get(pred, "O")
            
            if label.startswith("B-"):
                # Début d'une nouvelle entité
                if current_entity:
                    # Sauvegarder l'entité précédente
                    self.save_entity(structured_data, current_entity, current_text)
                
                current_entity = label[2:]  # Enlever le "B-"
                current_text = word
            
            elif label.startswith("I-") and current_entity == label[2:]:
                # Continuation de l'entité actuelle
                current_text += " " + word
            
            elif label == "O":
                # Pas d'entité
                if current_entity:
                    # Sauvegarder l'entité précédente
                    self.save_entity(structured_data, current_entity, current_text)
                    current_entity = None
                    current_text = ""
        
        # Sauvegarder la dernière entité si nécessaire
        if current_entity:
            self.save_entity(structured_data, current_entity, current_text)
        
        return structured_data
    
    def save_entity(self, structured_data, entity_type, text):
        """Sauvegarde une entité extraite dans le dictionnaire de données structurées"""
        text = text.strip()
        
        if not text:
            return
        
        if entity_type == "INVOICE_NUM":
            structured_data["numeroFacture"] = text
        elif entity_type == "DATE":
            # Attribuer la date au premier champ de date vide
            if not structured_data["datePiece"]:
                structured_data["datePiece"] = text
            elif not structured_data["dateCommande"]:
                structured_data["dateCommande"] = text
            elif not structured_data["dateLivraison"]:
                structured_data["dateLivraison"] = text
        elif entity_type == "TOTAL":
            # Essayer de déterminer s'il s'agit de TTC, HT ou TVA
            if "ttc" in text.lower() or "total" in text.lower():
                structured_data["totalTTC"] = self.extract_amount(text)
            elif "ht" in text.lower():
                structured_data["totalHT"] = self.extract_amount(text)
            elif "tva" in text.lower():
                structured_data["totalTVA"] = self.extract_amount(text)
            else:
                # Par défaut, considérer comme TTC
                structured_data["totalTTC"] = self.extract_amount(text)
        elif entity_type == "COMPANY":
            structured_data["client"]["societe"] = text
        # Ajouter d'autres types d'entités selon les besoins
    
    def extract_amount(self, text):
        """Extrait un montant numérique d'un texte"""
        import re
        
        # Rechercher un montant avec ou sans symbole d'euro
        match = re.search(r'(\d+[,.]\d{2})\s*(?:€|EUR|EURO|EUROS)?', text)
        if match:
            return match.group(1).replace(',', '.')
        
        return None
    
    def calculate_confidence_scores(self, logits):
        """Calcule les scores de confiance pour chaque champ"""
        # Convertir les logits en probabilités avec softmax
        probs = torch.nn.functional.softmax(logits, dim=-1).cpu().numpy()
        
        # Calculer les scores de confiance moyens pour chaque type d'entité
        confidence_scores = {}
        
        # Initialiser les scores pour chaque type d'entité
        for label_id, label_name in self.label_map.items():
            if label_name.startswith("B-"):
                entity_type = label_name[2:]
                confidence_scores[entity_type] = 0.0
        
        # Calculer les scores moyens
        for label_id, label_name in self.label_map.items():
            if label_name.startswith("B-"):
                entity_type = label_name[2:]
                # Prendre la probabilité maximale pour ce type d'entité
                max_prob = np.max(probs[:, label_id])
                confidence_scores[entity_type] = float(max_prob)
        
        return confidence_scores
    
    def train(self, annotations, epochs=3, batch_size=4):
        """Entraîne le modèle sur les annotations fournies"""
        if self.processor is None or self.model is None:
            logger.error("Le modèle LayoutLMv3 n'est pas chargé")
            return {"error": "Modèle non disponible"}
        
        try:
            # Préparer le dataset
            dataset = InvoiceDataset(annotations, self.processor)
            dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
            
            # Configurer l'optimiseur (utiliser l'implémentation PyTorch pour éviter l'avertissement)
            optimizer = torch.optim.AdamW(self.model.parameters(), lr=5e-5)
            
            # Mettre le modèle en mode entraînement
            self.model.train()
            
            # Boucle d'entraînement
            for epoch in range(epochs):
                total_loss = 0
                
                for batch in dataloader:
                    # Déplacer les tenseurs vers le device
                    for k, v in batch.items():
                        batch[k] = v.to(self.device)
                    
                    # Forward pass
                    outputs = self.model(**batch)
                    loss = outputs.loss
                    
                    # Backward pass
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
                
                logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(dataloader)}")
            
            # Sauvegarder le modèle
            os.makedirs(self.model_path, exist_ok=True)
            self.model.save_pretrained(self.model_path)
            self.processor.save_pretrained(self.model_path)
            
            return {
                "status": "success",
                "message": f"Modèle entraîné avec succès sur {len(annotations)} annotations"
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement du modèle: {str(e)}")
            return {"error": f"Erreur d'entraînement: {str(e)}"}

# Singleton pour éviter de recharger le modèle à chaque requête
layoutlmv3_extractor = LayoutLMv3Extractor()