from django.db import models
import json

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