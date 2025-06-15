from rest_framework import serializers
from .models import Invoice

class InvoiceSerializer(serializers.ModelSerializer):
    extracted_content = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = ['id', 'file', 'uploaded_at', 'processed', 'extracted_content']
        read_only_fields = ['uploaded_at', 'processed', 'extracted_content']
    
    def get_extracted_content(self, obj):
        """
        Récupère le contenu extrait de la facture
        
        Args:
            obj: Instance du modèle Invoice
            
        Returns:
            dict: Contenu extrait ou None si pas encore traité
        """
        return obj.get_extracted_text()