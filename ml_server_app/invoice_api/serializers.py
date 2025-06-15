from rest_framework import serializers
from .models import Invoice

class InvoiceSerializer(serializers.ModelSerializer):
    extracted_content = serializers.SerializerMethodField()
    formatted_text_url = serializers.SerializerMethodField()
    html_formatted_text_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = ['id', 'file', 'uploaded_at', 'processed', 'extracted_content', 
                 'formatted_text_url', 'html_formatted_text_url']
        read_only_fields = ['uploaded_at', 'processed', 'extracted_content', 
                           'formatted_text_url', 'html_formatted_text_url']
    
    def get_extracted_content(self, obj):
        """
        Récupère le contenu extrait de la facture
        
        Args:
            obj: Instance du modèle Invoice
            
        Returns:
            dict: Contenu extrait ou None si pas encore traité
        """
        return obj.get_extracted_text()
        
    def get_formatted_text_url(self, obj):
        """
        Récupère l'URL pour accéder au texte formaté
        
        Args:
            obj: Instance du modèle Invoice
            
        Returns:
            str: URL du texte formaté
        """
        request = self.context.get('request')
        if request and obj.processed:
            return request.build_absolute_uri(obj.get_formatted_text_url())
        return None
        
    def get_html_formatted_text_url(self, obj):
        """
        Récupère l'URL pour accéder au texte formaté en HTML
        
        Args:
            obj: Instance du modèle Invoice
            
        Returns:
            str: URL du texte formaté en HTML
        """
        request = self.context.get('request')
        if request and obj.processed:
            return request.build_absolute_uri(obj.get_html_formatted_text_url())
        return None