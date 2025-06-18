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
                # Utiliser des valeurs dans la plage 0-1000
                boxes = [[0, 0, 500, 500]] * len(words)
        else:
            # Faire l'OCR
            ocr_result = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang='fra+eng')
            words = [word for word in ocr_result['text'] if word.strip()]
            boxes = []
            
            # Obtenir les dimensions de l'image pour normaliser les coordonnées
            width, height = image.size
            
            for i in range(len(ocr_result['text'])):
                if ocr_result['text'][i].strip():
                    # Extraire les coordonnées
                    x, y, w, h = ocr_result['left'][i], ocr_result['top'][i], ocr_result['width'][i], ocr_result['height'][i]
                    
                    # Normaliser les coordonnées avec la fonction utilitaire
                    normalized_bbox = normalize_bbox([x, y, w, h], width, height)
                    
                    boxes.append(normalized_bbox)
        
        # Préparer les étiquettes pour chaque mot
        labels = []
        for word in words:
            # Logique pour attribuer des étiquettes en fonction des données annotées
            # Par exemple, vérifier si le mot correspond à un numéro de facture, une date, etc.
            # Pour simplifier, on utilise une étiquette générique ici
            labels.append(0)  # 0 = autre, 1 = numéro de facture, 2 = date, etc.
        
        try:
            # Vérifier que toutes les boîtes sont dans la plage 0-1000
            for i, box in enumerate(boxes):
                if not all(0 <= coord <= 1000 for coord in box):
                    logger.warning(f"Boîte hors plage détectée: {box}, normalisation forcée")
                    boxes[i] = [max(0, min(coord, 1000)) for coord in box]
                    
                # S'assurer que x2 > x1 et y2 > y1
                if boxes[i][2] <= boxes[i][0]:
                    boxes[i][2] = min(boxes[i][0] + 10, 1000)
                if boxes[i][3] <= boxes[i][1]:
                    boxes[i][3] = min(boxes[i][1] + 10, 1000)
            
            # Encoder les entrées - utiliser une approche différente pour éviter les problèmes
            # Créer les entrées séparément
            image_features = self.processor.image_processor(images=image, return_tensors="pt")
            encoding = self.processor.tokenizer(
                text=words,
                boxes=boxes,
                truncation=True,
                padding="max_length",
                max_length=self.max_length,
                return_tensors="pt"
            )
            
            # Fusionner les entrées
            for k, v in image_features.items():
                encoding[k] = v
            
            # Créer des étiquettes de la même taille que les tokens
            # Le tokenizer peut créer plus de tokens que de mots d'origine
            input_ids_length = encoding["input_ids"].shape[1]
            
            # Créer un tenseur d'étiquettes de la bonne taille (rempli de 0)
            token_labels = torch.zeros(input_ids_length, dtype=torch.long)
            
            # Ajouter les étiquettes
            encoding["labels"] = token_labels
            
            # Supprimer la dimension batch
            for k, v in encoding.items():
                encoding[k] = v.squeeze()
                
            return encoding
        except Exception as e:
            logger.error(f"Erreur lors de l'encodage des entrées: {str(e)}")
            # Retourner un encodage vide en cas d'erreur
            return {
                "input_ids": torch.zeros(self.max_length, dtype=torch.long),
                "attention_mask": torch.zeros(self.max_length, dtype=torch.long),
                "bbox": torch.zeros((self.max_length, 4), dtype=torch.long),
                "pixel_values": torch.zeros((3, 224, 224), dtype=torch.float),
                "labels": torch.zeros(self.max_length, dtype=torch.long)
            }

def normalize_bbox(bbox, width, height):
    """
    Normalise les coordonnées d'une boîte délimitante dans la plage 0-1000
    
    Args:
        bbox: Liste [x, y, w, h] ou [x, y, x2, y2]
        width: Largeur de l'image
        height: Hauteur de l'image
        
    Returns:
        Liste [x_norm, y_norm, x2_norm, y2_norm] avec des valeurs entre 0 et 1000
    """
    # Vérifier si le format est [x, y, w, h] ou [x, y, x2, y2]
    if len(bbox) == 4:
        if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:  # Format [x, y, w, h]
            x, y, w, h = bbox
            x2, y2 = x + w, y + h
        else:  # Format [x, y, x2, y2]
            x, y, x2, y2 = bbox
    else:
        # Format invalide, utiliser des valeurs par défaut
        return [0, 0, 1000, 1000]
    
    # Normaliser les coordonnées entre 0 et 1000
    x_norm = int(x * 1000 / width) if width > 0 else 0
    y_norm = int(y * 1000 / height) if height > 0 else 0
    x2_norm = int(x2 * 1000 / width) if width > 0 else 1000
    y2_norm = int(y2 * 1000 / height) if height > 0 else 1000
    
    # S'assurer que les coordonnées sont dans la plage 0-1000
    x_norm = max(0, min(x_norm, 1000))
    y_norm = max(0, min(y_norm, 1000))
    x2_norm = max(0, min(x2_norm, 1000))
    y2_norm = max(0, min(y2_norm, 1000))
    
    # S'assurer que x2 > x1 et y2 > y1
    if x2_norm <= x_norm:
        x2_norm = min(x_norm + 10, 1000)
    if y2_norm <= y_norm:
        y2_norm = min(y_norm + 10, 1000)
    
    return [x_norm, y_norm, x2_norm, y2_norm]

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
            # Configuration spécifique pour le processeur
            processor_kwargs = {
                "apply_ocr": False,  # Crucial: désactiver l'OCR intégré
                "ocr_lang": ["fra", "eng"]
            }
            
            # Vérifier si un modèle personnalisé existe
            if os.path.exists(self.model_path) and os.path.isdir(self.model_path):
                try:
                    logger.info(f"Chargement du modèle personnalisé depuis {self.model_path}")
                    self.processor = LayoutLMv3Processor.from_pretrained(
                        self.model_path,
                        **processor_kwargs
                    )
                    self.model = LayoutLMv3ForTokenClassification.from_pretrained(self.model_path)
                except Exception as e:
                    logger.error(f"Erreur lors du chargement du modèle personnalisé: {str(e)}")
                    logger.info("Utilisation du modèle pré-entraîné par défaut")
                    # Si le chargement échoue, utiliser le modèle pré-entraîné
                    self.processor = LayoutLMv3Processor.from_pretrained(
                        "microsoft/layoutlmv3-base",
                        **processor_kwargs
                    )
                    self.model = LayoutLMv3ForTokenClassification.from_pretrained(
                        "microsoft/layoutlmv3-base",
                        num_labels=len(self.label_map)
                    )
            else:
                # Utiliser le modèle pré-entraîné par défaut
                logger.info("Chargement du modèle pré-entraîné LayoutLMv3")
                self.processor = LayoutLMv3Processor.from_pretrained(
                    "microsoft/layoutlmv3-base",
                    **processor_kwargs
                )
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
            
            # Obtenir les dimensions de l'image pour normaliser les coordonnées
            width, height = image.size
            
            for i in range(len(ocr_result['text'])):
                if ocr_result['text'][i].strip():
                    words.append(ocr_result['text'][i])
                    
                    # Extraire les coordonnées
                    x, y, w, h = ocr_result['left'][i], ocr_result['top'][i], ocr_result['width'][i], ocr_result['height'][i]
                    
                    # Normaliser les coordonnées avec la fonction utilitaire
                    normalized_bbox = normalize_bbox([x, y, w, h], width, height)
                    
                    boxes.append(normalized_bbox)
            
            # Vérifier que toutes les boîtes sont dans la plage 0-1000
            for i, box in enumerate(boxes):
                if not all(0 <= coord <= 1000 for coord in box):
                    logger.warning(f"Boîte hors plage détectée: {box}, normalisation forcée")
                    boxes[i] = [max(0, min(coord, 1000)) for coord in box]
                    
                # S'assurer que x2 > x1 et y2 > y1
                if boxes[i][2] <= boxes[i][0]:
                    boxes[i][2] = min(boxes[i][0] + 10, 1000)
                if boxes[i][3] <= boxes[i][1]:
                    boxes[i][3] = min(boxes[i][1] + 10, 1000)
            
            # Encoder les entrées - utiliser une approche différente pour éviter les problèmes
            # Créer les entrées séparément
            image_features = self.processor.image_processor(images=image, return_tensors="pt")
            text_features = self.processor.tokenizer(
                text=words,
                boxes=boxes,
                truncation=True,
                padding="max_length",
                max_length=512,
                return_tensors="pt"
            )
            
            # Fusionner les entrées
            encoding = text_features.copy()
            for k, v in image_features.items():
                encoding[k] = v
            
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
            
            # Sauvegarder le modèle dans un répertoire temporaire puis le copier
            with tempfile.TemporaryDirectory() as temp_dir:
                # Sauvegarder dans le répertoire temporaire
                logger.info(f"Sauvegarde du modèle dans le répertoire temporaire: {temp_dir}")
                self.model.save_pretrained(temp_dir)
                self.processor.save_pretrained(temp_dir)
                
                # Supprimer l'ancien modèle s'il existe
                if os.path.exists(self.model_path):
                    logger.info(f"Suppression de l'ancien modèle: {self.model_path}")
                    import shutil
                    shutil.rmtree(self.model_path, ignore_errors=True)
                
                # Créer le répertoire de destination
                os.makedirs(self.model_path, exist_ok=True)
                
                # Copier les fichiers du répertoire temporaire vers le répertoire de destination
                logger.info(f"Copie du modèle vers: {self.model_path}")
                import shutil
                for item in os.listdir(temp_dir):
                    s = os.path.join(temp_dir, item)
                    d = os.path.join(self.model_path, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)
            
            return {
                "status": "success",
                "message": f"Modèle entraîné avec succès sur {len(annotations)} annotations"
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement du modèle: {str(e)}")
            return {"error": f"Erreur d'entraînement: {str(e)}"}

# Singleton pour éviter de recharger le modèle à chaque requête
layoutlmv3_extractor = LayoutLMv3Extractor()