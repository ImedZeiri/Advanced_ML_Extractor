from django.db import models
from django.utils import timezone

class Invoice(models.Model):
    """Modèle pour stocker les informations des factures extraites"""
    
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('processing', 'En cours de traitement'),
        ('completed', 'Traitement terminé'),
        ('failed', 'Échec du traitement'),
    )
    
    original_file = models.FileField(upload_to='invoices/original/')
    processed_file = models.FileField(upload_to='invoices/processed/', null=True, blank=True)
    
    # Métadonnées
    upload_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processing_time = models.FloatField(null=True, blank=True)
    
    # Données extraites
    extracted_data = models.JSONField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    
    # Informations de la facture
    invoice_number = models.CharField(max_length=100, null=True, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vendor_name = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"Facture {self.id} - {self.vendor_name or 'Inconnu'} - {self.status}"