import time
import os
import json
import logging
from django.utils import timezone
from .models import Invoice
from .ml_pipeline import InvoiceExtractionPipeline

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_invoice(invoice_id):
    """
    Traite une facture en utilisant le pipeline d'extraction ML
    
    Dans un environnement de production, cette fonction serait une tâche Celery
    """
    try:
        # Récupération de l'instance de facture
        invoice = Invoice.objects.get(id=invoice_id)
        logger.info(f"Début du traitement de la facture ID: {invoice_id}")
        
        # Mise à jour du statut
        invoice.status = 'processing'
        invoice.save()
        
        # Mesure du temps de traitement
        start_time = time.time()
        
        # Initialisation du pipeline d'extraction
        pipeline = InvoiceExtractionPipeline()
        
        # Traitement de la facture
        extracted_data = pipeline.process(invoice.original_file.path)
        
        # Calcul du temps de traitement
        processing_time = time.time() - start_time
        logger.info(f"Traitement terminé en {processing_time:.2f} secondes")
        
        # Mise à jour des données extraites
        invoice.extracted_data = extracted_data
        invoice.processing_time = processing_time
        
        # Vérification des erreurs
        if 'error' in extracted_data:
            invoice.status = 'failed'
            logger.error(f"Échec du traitement: {extracted_data['error']}")
        else:
            invoice.status = 'completed'
            logger.info("Traitement réussi")
            
            # Extraction des champs spécifiques
            if 'invoice_number' in extracted_data:
                invoice.invoice_number = extracted_data['invoice_number']
            if 'invoice_date' in extracted_data:
                invoice.invoice_date = extracted_data['invoice_date']
            if 'due_date' in extracted_data:
                invoice.due_date = extracted_data['due_date']
            if 'total_amount' in extracted_data:
                invoice.total_amount = extracted_data['total_amount']
            if 'tax_amount' in extracted_data:
                invoice.tax_amount = extracted_data['tax_amount']
            if 'vendor_name' in extracted_data:
                invoice.vendor_name = extracted_data['vendor_name']
            if 'confidence_score' in extracted_data:
                invoice.confidence_score = extracted_data['confidence_score']
        
        invoice.save()
        logger.info(f"Données de la facture ID: {invoice_id} mises à jour")
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la facture ID: {invoice_id}: {str(e)}")
        try:
            # En cas d'erreur, mise à jour du statut
            invoice = Invoice.objects.get(id=invoice_id)
            invoice.status = 'failed'
            invoice.extracted_data = {'error': str(e)}
            invoice.save()
        except Exception as inner_e:
            logger.error(f"Erreur lors de la mise à jour du statut d'échec: {str(inner_e)}")