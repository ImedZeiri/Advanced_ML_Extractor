"""
Module pour l'extraction de données à partir de factures en utilisant des modèles de ML
"""
import os
import logging
import json
from datetime import datetime

logger = logging.getLogger("invoice_extractor")

class MLExtractor:
    """
    Classe pour extraire des données à partir de factures en utilisant des modèles de ML
    """
    
    def __init__(self):
        """
        Initialise l'extracteur ML
        """
        self.models_loaded = False
        self.transformers_available = False
        self.spacy_available = False
        
        # Vérifier si les bibliothèques nécessaires sont disponibles
        try:
            import transformers
            self.transformers_available = True
            logger.info("Bibliothèque transformers disponible")
        except ImportError:
            logger.warning("Bibliothèque transformers non disponible")
        
        try:
            import spacy
            self.spacy_available = True
            logger.info("Bibliothèque spaCy disponible")
        except ImportError:
            logger.warning("Bibliothèque spaCy non disponible")
        
        # Charger les modèles si disponibles
        if self.transformers_available:
            try:
                self._load_transformers_models()
            except Exception as e:
                logger.error(f"Erreur lors du chargement des modèles transformers: {str(e)}")
        
        if self.spacy_available:
            try:
                self._load_spacy_models()
            except Exception as e:
                logger.error(f"Erreur lors du chargement des modèles spaCy: {str(e)}")
    
    def _load_transformers_models(self):
        """
        Charge les modèles transformers
        """
        try:
            from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
            
            # Modèle pour la reconnaissance d'entités nommées (NER)
            self.tokenizer = AutoTokenizer.from_pretrained("dbmdz/bert-large-cased-finetuned-conll03-english")
            self.model = AutoModelForTokenClassification.from_pretrained("dbmdz/bert-large-cased-finetuned-conll03-english")
            self.ner_pipeline = pipeline("ner", model=self.model, tokenizer=self.tokenizer, aggregation_strategy="simple")
            
            # Modèle pour la classification de documents
            self.doc_classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")
            
            self.models_loaded = True
            logger.info("Modèles transformers chargés avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des modèles transformers: {str(e)}")
            self.models_loaded = False
    
    def _load_spacy_models(self):
        """
        Charge les modèles spaCy
        """
        try:
            import spacy
            
            # Charger les modèles français et anglais
            self.nlp_fr = spacy.load("fr_core_news_lg")
            self.nlp_en = spacy.load("en_core_web_lg")
            
            logger.info("Modèles spaCy chargés avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des modèles spaCy: {str(e)}")
    
    def extract_entities_with_spacy(self, text):
        """
        Extrait les entités nommées avec spaCy
        
        Args:
            text: Texte à analyser
            
        Returns:
            dict: Entités extraites
        """
        if not self.spacy_available:
            logger.warning("spaCy n'est pas disponible")
            return {}
        
        # Détecter la langue
        # Utiliser un échantillon pour la détection de langue (plus rapide)
        sample = text[:1000] if len(text) > 1000 else text
        
        try:
            # Analyser avec le modèle français
            doc_fr = self.nlp_fr(sample)
            # Analyser avec le modèle anglais
            doc_en = self.nlp_en(sample)
            
            # Choisir le modèle avec le meilleur score
            if doc_fr.cats.get('fr', 0) > doc_en.cats.get('en', 0):
                logger.info("Langue détectée: français")
                doc = self.nlp_fr(text)
            else:
                logger.info("Langue détectée: anglais")
                doc = self.nlp_en(text)
            
            # Extraire les entités
            entities = {}
            for ent in doc.ents:
                if ent.label_ not in entities:
                    entities[ent.label_] = []
                entities[ent.label_].append({
                    "text": ent.text,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
            
            # Extraire les montants (nombres suivis de symboles monétaires)
            amounts = []
            for token in doc:
                if token.like_num and token.i + 1 < len(doc) and doc[token.i + 1].text in ["€", "EUR", "euro", "euros"]:
                    amounts.append({
                        "text": token.text + " " + doc[token.i + 1].text,
                        "value": token.text
                    })
            
            if amounts:
                entities["MONEY"] = amounts
            
            return entities
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction d'entités avec spaCy: {str(e)}")
            return {}
    
    def extract_entities_with_transformers(self, text):
        """
        Extrait les entités nommées avec transformers
        
        Args:
            text: Texte à analyser
            
        Returns:
            dict: Entités extraites
        """
        if not self.transformers_available or not self.models_loaded:
            logger.warning("transformers n'est pas disponible ou les modèles ne sont pas chargés")
            return {}
        
        try:
            # Limiter la taille du texte pour éviter les erreurs de mémoire
            max_length = 512
            if len(text) > max_length:
                logger.info(f"Texte tronqué de {len(text)} à {max_length} caractères pour l'analyse transformers")
                text = text[:max_length]
            
            # Extraire les entités
            entities = self.ner_pipeline(text)
            
            # Regrouper par type d'entité
            grouped_entities = {}
            for entity in entities:
                entity_type = entity["entity_group"]
                if entity_type not in grouped_entities:
                    grouped_entities[entity_type] = []
                
                grouped_entities[entity_type].append({
                    "text": entity["word"],
                    "score": entity["score"],
                    "start": entity["start"],
                    "end": entity["end"]
                })
            
            return grouped_entities
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction d'entités avec transformers: {str(e)}")
            return {}
    
    def extract_invoice_data(self, text):
        """
        Extrait les données de facture en utilisant les modèles ML
        
        Args:
            text: Texte de la facture
            
        Returns:
            dict: Données extraites
        """
        result = {
            "ml_extraction": {
                "timestamp": datetime.now().isoformat(),
                "entities": {}
            }
        }
        
        # Extraire les entités avec spaCy
        if self.spacy_available:
            spacy_entities = self.extract_entities_with_spacy(text)
            result["ml_extraction"]["entities"]["spacy"] = spacy_entities
        
        # Extraire les entités avec transformers
        if self.transformers_available and self.models_loaded:
            transformers_entities = self.extract_entities_with_transformers(text)
            result["ml_extraction"]["entities"]["transformers"] = transformers_entities
        
        # Analyser les entités pour extraire les informations de facture
        extracted_data = self._analyze_entities(result["ml_extraction"]["entities"], text)
        result["ml_extraction"]["extracted_data"] = extracted_data
        
        return result
    
    def _analyze_entities(self, entities, text):
        """
        Analyse les entités pour extraire les informations de facture
        
        Args:
            entities: Entités extraites
            text: Texte original
            
        Returns:
            dict: Informations de facture
        """
        invoice_data = {
            "invoice_number": None,
            "date": None,
            "total_amount": None,
            "company_name": None,
            "client_name": None
        }
        
        # Analyser les entités spaCy
        spacy_entities = entities.get("spacy", {})
        
        # Extraire le numéro de facture
        if "PRODUCT" in spacy_entities:
            for entity in spacy_entities["PRODUCT"]:
                if "facture" in entity["text"].lower() or "invoice" in entity["text"].lower():
                    invoice_data["invoice_number"] = entity["text"]
                    break
        
        # Extraire la date
        if "DATE" in spacy_entities:
            invoice_data["date"] = spacy_entities["DATE"][0]["text"] if spacy_entities["DATE"] else None
        
        # Extraire le montant total
        if "MONEY" in spacy_entities:
            invoice_data["total_amount"] = spacy_entities["MONEY"][0]["text"] if spacy_entities["MONEY"] else None
        
        # Extraire le nom de l'entreprise
        if "ORG" in spacy_entities:
            invoice_data["company_name"] = spacy_entities["ORG"][0]["text"] if spacy_entities["ORG"] else None
        
        # Extraire le nom du client
        if "PERSON" in spacy_entities:
            invoice_data["client_name"] = spacy_entities["PERSON"][0]["text"] if spacy_entities["PERSON"] else None
        
        # Analyser les entités transformers
        transformers_entities = entities.get("transformers", {})
        
        # Compléter avec les entités transformers si nécessaires
        if not invoice_data["company_name"] and "ORG" in transformers_entities:
            invoice_data["company_name"] = transformers_entities["ORG"][0]["text"] if transformers_entities["ORG"] else None
        
        if not invoice_data["client_name"] and "PER" in transformers_entities:
            invoice_data["client_name"] = transformers_entities["PER"][0]["text"] if transformers_entities["PER"] else None
        
        return invoice_data