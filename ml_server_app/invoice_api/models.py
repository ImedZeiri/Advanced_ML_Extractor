from django.db import models
import json
from django.urls import reverse
from django.utils import timezone

class Invoice(models.Model):
    file = models.FileField(upload_to='invoices/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    extracted_text = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Invoice {self.id} - {self.uploaded_at}"
    
    def set_extracted_text(self, text_data):
        """
        Stocke les données de texte extraites au format JSON
        
        Args:
            text_data: Dictionnaire contenant le texte extrait et les métadonnées
        """
        self.extracted_text = json.dumps(text_data)
        self.processed = True
        self.save()
    
    def get_extracted_text(self):
        """
        Récupère les données de texte extraites au format dictionnaire
        
        Returns:
            dict: Dictionnaire contenant le texte extrait et les métadonnées
        """
        if self.extracted_text:
            return json.loads(self.extracted_text)
        return None
        
    def get_formatted_text_url(self):
        """
        Retourne l'URL pour accéder au texte formaté
        
        Returns:
            str: URL du texte formaté
        """
        return reverse('invoice-formatted-text', kwargs={'pk': self.pk})
        
    def get_html_formatted_text_url(self):
        """
        Retourne l'URL pour accéder au texte formaté en HTML
        
        Returns:
            str: URL du texte formaté en HTML
        """
        return f"{reverse('invoice-formatted-text', kwargs={'pk': self.pk})}?format=html"

class InvoiceAnnotation(models.Model):
    """Modèle pour stocker les annotations de factures pour l'entraînement"""
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='annotations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Données originales et corrigées
    original_data = models.TextField()
    corrected_data = models.TextField()
    
    # Métadonnées
    used_for_training = models.BooleanField(default=False)
    training_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Annotation for Invoice {self.invoice.id} - {self.created_at}"
    
    def get_original_data(self):
        """Récupère les données originales au format dictionnaire"""
        return json.loads(self.original_data)
    
    def get_corrected_data(self):
        """Récupère les données corrigées au format dictionnaire"""
        return json.loads(self.corrected_data)
    
    def set_original_data(self, data):
        """Stocke les données originales au format JSON"""
        self.original_data = json.dumps(data)
    
    def set_corrected_data(self, data):
        """Stocke les données corrigées au format JSON"""
        self.corrected_data = json.dumps(data)
    
    def mark_as_trained(self):
        """Marque l'annotation comme utilisée pour l'entraînement"""
        self.used_for_training = True
        self.training_date = timezone.now()
        self.save()

class TrainingJob(models.Model):
    """Modèle pour suivre les jobs d'entraînement"""
    
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('running', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    annotations = models.ManyToManyField(InvoiceAnnotation, related_name='training_jobs')
    
    # Métadonnées
    epochs = models.IntegerField(default=3)
    batch_size = models.IntegerField(default=4)
    learning_rate = models.FloatField(default=5e-5)
    
    # Résultats
    results = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Training Job {self.id} - {self.status}"
    
    def get_results(self):
        """Récupère les résultats au format dictionnaire"""
        if self.results:
            return json.loads(self.results)
        return None
    
    def set_results(self, data):
        """Stocke les résultats au format JSON"""
        self.results = json.dumps(data)
        self.save()