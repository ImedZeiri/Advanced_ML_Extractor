from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Invoice
from .tasks import process_invoice
import time

@receiver(post_save, sender=Invoice)
def trigger_invoice_processing(sender, instance, created, **kwargs):
    """Déclenche le traitement de la facture après sa création"""
    if created:
        # Dans un environnement de production, on utiliserait Celery ou un autre système de tâches asynchrones
        # Pour simplifier, on appelle directement la fonction de traitement
        process_invoice(instance.id)