"""
Module pour la validation des données extraites des factures
"""
import re
from datetime import datetime
import logging

logger = logging.getLogger("invoice_extractor")

class DataValidator:
    """
    Classe pour valider les données extraites des factures
    """
    
    @staticmethod
    def validate_date(date_str):
        """
        Valide et normalise une date
        
        Args:
            date_str: Chaîne de caractères représentant une date
            
        Returns:
            str: Date normalisée au format JJ/MM/AAAA ou None si invalide
        """
        if not date_str:
            return None
            
        # Patterns de dates courants
        patterns = [
            # JJ/MM/AAAA
            r'^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$',
            # JJ/MM/AA
            r'^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2})$',
            # AAAA/MM/JJ
            r'^(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})$',
            # MM/JJ/AAAA (format US)
            r'^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, date_str)
            if match:
                groups = match.groups()
                
                # Format JJ/MM/AAAA ou JJ/MM/AA
                if len(groups[2]) == 4:
                    day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                elif len(groups[2]) == 2:
                    day, month, year = int(groups[0]), int(groups[1]), 2000 + int(groups[2])
                # Format AAAA/MM/JJ
                elif len(groups[0]) == 4:
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                else:
                    continue
                
                # Vérifier si la date est valide
                try:
                    date_obj = datetime(year, month, day)
                    # Vérifier si la date est dans une plage raisonnable
                    current_year = datetime.now().year
                    if year < 2000 or year > current_year + 1:
                        logger.warning(f"Date {date_str} a une année suspecte: {year}")
                        continue
                    
                    # Retourner au format JJ/MM/AAAA
                    return f"{day:02d}/{month:02d}/{year}"
                except ValueError:
                    logger.warning(f"Date invalide: {date_str}")
                    continue
        
        return None
    
    @staticmethod
    def validate_amount(amount_str):
        """
        Valide et normalise un montant
        
        Args:
            amount_str: Chaîne de caractères représentant un montant
            
        Returns:
            float: Montant normalisé ou None si invalide
        """
        if not amount_str:
            return None
            
        # Nettoyer la chaîne
        amount_str = amount_str.replace(' ', '')
        
        # Pattern pour les montants (avec virgule ou point)
        pattern = r'^(\d+[.,]\d{2})$'
        match = re.match(pattern, amount_str)
        
        if match:
            # Normaliser le séparateur décimal
            normalized = match.group(1).replace(',', '.')
            try:
                amount = float(normalized)
                # Vérifier si le montant est dans une plage raisonnable
                if amount < 0 or amount > 1000000:
                    logger.warning(f"Montant suspect: {amount}")
                    return None
                return amount
            except ValueError:
                logger.warning(f"Montant invalide: {amount_str}")
                return None
        
        return None
    
    @staticmethod
    def validate_invoice_number(invoice_number):
        """
        Valide un numéro de facture
        
        Args:
            invoice_number: Chaîne de caractères représentant un numéro de facture
            
        Returns:
            str: Numéro de facture normalisé ou None si invalide
        """
        if not invoice_number:
            return None
            
        # Nettoyer la chaîne
        invoice_number = invoice_number.strip()
        
        # Vérifier la longueur minimale
        if len(invoice_number) < 3:
            logger.warning(f"Numéro de facture trop court: {invoice_number}")
            return None
            
        # Vérifier si le numéro contient au moins un chiffre
        if not re.search(r'\d', invoice_number):
            logger.warning(f"Numéro de facture sans chiffre: {invoice_number}")
            return None
            
        return invoice_number
    
    @staticmethod
    def validate_structured_data(data):
        """
        Valide et normalise les données structurées extraites
        
        Args:
            data: Dictionnaire contenant les données structurées
            
        Returns:
            dict: Données structurées validées et normalisées
        """
        validated_data = data.copy()
        
        # Valider la date de la pièce
        if data.get("datePiece"):
            validated_data["datePiece"] = DataValidator.validate_date(data["datePiece"])
            
        # Valider la date de commande
        if data.get("dateCommande"):
            validated_data["dateCommande"] = DataValidator.validate_date(data["dateCommande"])
            
        # Valider la date de livraison
        if data.get("dateLivraison"):
            validated_data["dateLivraison"] = DataValidator.validate_date(data["dateLivraison"])
            
        # Valider le numéro de facture
        if data.get("numeroFacture"):
            validated_data["numeroFacture"] = DataValidator.validate_invoice_number(data["numeroFacture"])
            
        # Valider les montants
        if data.get("totalTTC"):
            validated_data["totalTTC"] = DataValidator.validate_amount(data["totalTTC"])
            
        if data.get("totalHT"):
            validated_data["totalHT"] = DataValidator.validate_amount(data["totalHT"])
            
        if data.get("totalTVA"):
            validated_data["totalTVA"] = DataValidator.validate_amount(data["totalTVA"])
            
        # Valider la cohérence des montants
        if validated_data.get("totalTTC") and validated_data.get("totalHT") and validated_data.get("totalTVA"):
            ttc = validated_data["totalTTC"]
            ht = validated_data["totalHT"]
            tva = validated_data["totalTVA"]
            
            # Vérifier si TTC = HT + TVA (avec une marge d'erreur)
            if abs((ht + tva) - ttc) > 0.1:
                logger.warning(f"Incohérence dans les montants: TTC={ttc}, HT={ht}, TVA={tva}")
                
                # Essayer de corriger
                if abs(ht + tva - ttc) < 1.0:
                    logger.info(f"Correction automatique du montant TTC: {ttc} -> {ht + tva}")
                    validated_data["totalTTC"] = ht + tva
        
        # Valider les articles
        if data.get("articles"):
            for i, article in enumerate(data["articles"]):
                if article.get("quantite"):
                    try:
                        validated_data["articles"][i]["quantite"] = float(article["quantite"].replace(',', '.'))
                    except (ValueError, AttributeError):
                        validated_data["articles"][i]["quantite"] = None
                        
                if article.get("prixHT"):
                    validated_data["articles"][i]["prixHT"] = DataValidator.validate_amount(article["prixHT"])
                    
                if article.get("totalHT"):
                    validated_data["articles"][i]["totalHT"] = DataValidator.validate_amount(article["totalHT"])
        
        # Ajouter un score de confiance global
        validated_data["confidence_score"] = DataValidator.calculate_confidence_score(validated_data)
        
        return validated_data
    
    @staticmethod
    def calculate_confidence_score(data):
        """
        Calcule un score de confiance pour les données extraites
        
        Args:
            data: Dictionnaire contenant les données structurées
            
        Returns:
            float: Score de confiance entre 0 et 1
        """
        score = 0
        total_fields = 7  # Nombre de champs principaux
        
        # Vérifier les champs principaux
        if data.get("numeroFacture"):
            score += 1
        if data.get("datePiece"):
            score += 1
        if data.get("totalTTC"):
            score += 1
        if data.get("totalHT"):
            score += 1
        if data.get("totalTVA"):
            score += 1
        if data.get("client") and data["client"].get("societe"):
            score += 1
        if data.get("articles") and len(data["articles"]) > 0:
            score += 1
            
        return score / total_fields