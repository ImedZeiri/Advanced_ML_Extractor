from django.db import models
from django.utils import timezone
import os
import uuid

class InvoiceTemplate(models.Model):
    """Modèle pour stocker les templates de factures"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    vendor = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Champs pour les règles d'extraction
    amount_regex = models.CharField(max_length=255, blank=True, null=True)
    date_regex = models.CharField(max_length=255, blank=True, null=True)
    invoice_number_regex = models.CharField(max_length=255, blank=True, null=True)
    tax_regex = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"{self.vendor} - {self.name}"

def invoice_upload_path(instance, filename):
    """Définit le chemin d'upload pour les factures"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('invoices', filename)

class Invoice(models.Model):
    """Modèle pour stocker les factures et leurs métadonnées"""
    STATUS_CHOICES = (
        ('pending', 'En attente de traitement'),
        ('processing', 'En cours de traitement'),
        ('completed', 'Traitement terminé'),
        ('error', 'Erreur de traitement'),
    )
    
    file = models.FileField(upload_to=invoice_upload_path)
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    
    # Métadonnées extraites
    vendor_name = models.CharField(max_length=255, blank=True, null=True)
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    invoice_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, blank=True, null=True)
    
    # Données brutes extraites (JSON)
    extracted_data = models.JSONField(null=True, blank=True)
    
    # Lien vers le template utilisé (si applicable)
    template = models.ForeignKey(InvoiceTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Invoice {self.invoice_number or self.id} - {self.vendor_name or 'Unknown'}"
    
    def mark_as_processing(self):
        self.status = 'processing'
        self.save()
    
    def mark_as_completed(self, extracted_data=None):
        self.status = 'completed'
        self.processed_at = timezone.now()
        if extracted_data:
            self.extracted_data = extracted_data
            # Mise à jour des champs spécifiques
            self.vendor_name = extracted_data.get('vendor_name')
            self.invoice_number = extracted_data.get('invoice_number')
            self.invoice_date = extracted_data.get('invoice_date')
            self.due_date = extracted_data.get('due_date')
            self.total_amount = extracted_data.get('total_amount')
            self.tax_amount = extracted_data.get('tax_amount')
            self.currency = extracted_data.get('currency')
        self.save()
    
    def mark_as_error(self, error_message):
        self.status = 'error'
        self.error_message = error_message
        self.processed_at = timezone.now()
        self.save()

class InvoiceLineItem(models.Model):
    """Modèle pour stocker les lignes de facture"""
    invoice = models.ForeignKey(Invoice, related_name='line_items', on_delete=models.CASCADE)
    description = models.TextField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.description[:30]}... - {self.total_price}"

class TrainingData(models.Model):
    """Modèle pour stocker les données d'entraînement annotées"""
    file = models.FileField(upload_to='training_data')
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    annotations = models.JSONField(null=True, blank=True)
    dataset_type = models.CharField(max_length=50, choices=[
        ('funsd', 'FUNSD Dataset'),
        ('invoice2data', 'Invoice2Data Dataset'),
        ('custom', 'Custom Dataset')
    ])
    is_validated = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.original_filename} - {self.dataset_type}"