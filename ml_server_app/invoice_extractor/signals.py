from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import os
import logging

from .models import Invoice, TrainingData

# Configuration du logger
logger = logging.getLogger(__name__)

@receiver(post_delete, sender=Invoice)
def auto_delete_invoice_file_on_delete(sender, instance, **kwargs):
    """
    Supprime le fichier de facture lorsque l'objet Invoice est supprimé
    """
    try:
        if instance.file:
            if os.path.isfile(instance.file.path):
                os.remove(instance.file.path)
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du fichier de facture: {str(e)}")

@receiver(post_delete, sender=TrainingData)
def auto_delete_training_data_file_on_delete(sender, instance, **kwargs):
    """
    Supprime le fichier de données d'entraînement lorsque l'objet TrainingData est supprimé
    """
    try:
        if instance.file:
            if os.path.isfile(instance.file.path):
                os.remove(instance.file.path)
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du fichier de données d'entraînement: {str(e)}")

@receiver(post_save, sender=Invoice)
def process_invoice_on_create(sender, instance, created, **kwargs):
    """
    Traite la facture lorsqu'elle est créée
    
    Note: Dans un cas réel, on utiliserait Celery pour le traitement asynchrone
    """
    # Cette fonction est un placeholder pour le traitement asynchrone
    # Dans un cas réel, on utiliserait Celery
    pass