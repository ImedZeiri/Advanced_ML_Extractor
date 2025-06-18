from rest_framework import serializers
from .models import Invoice, InvoiceAnnotation, TrainingJob

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

class InvoiceAnnotationSerializer(serializers.ModelSerializer):
    original_data = serializers.JSONField(source='get_original_data')
    corrected_data = serializers.JSONField(source='get_corrected_data')
    invoice_file = serializers.SerializerMethodField()
    
    class Meta:
        model = InvoiceAnnotation
        fields = ['id', 'invoice', 'invoice_file', 'created_at', 'updated_at', 
                 'original_data', 'corrected_data', 'used_for_training', 'training_date']
        read_only_fields = ['created_at', 'updated_at', 'used_for_training', 'training_date']
    
    def get_invoice_file(self, obj):
        """Récupère l'URL du fichier de facture"""
        request = self.context.get('request')
        if request and obj.invoice.file:
            return request.build_absolute_uri(obj.invoice.file.url)
        return None
    
    def create(self, validated_data):
        """Crée une nouvelle annotation avec les données originales et corrigées"""
        original_data = validated_data.pop('get_original_data', {})
        corrected_data = validated_data.pop('get_corrected_data', {})
        
        annotation = InvoiceAnnotation.objects.create(**validated_data)
        annotation.set_original_data(original_data)
        annotation.set_corrected_data(corrected_data)
        annotation.save()
        
        return annotation
    
    def update(self, instance, validated_data):
        """Met à jour une annotation existante"""
        if 'get_original_data' in validated_data:
            instance.set_original_data(validated_data.pop('get_original_data'))
        
        if 'get_corrected_data' in validated_data:
            instance.set_corrected_data(validated_data.pop('get_corrected_data'))
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class TrainingJobSerializer(serializers.ModelSerializer):
    results = serializers.JSONField(source='get_results', read_only=True)
    annotations_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TrainingJob
        fields = ['id', 'created_at', 'updated_at', 'status', 'annotations', 
                 'annotations_count', 'epochs', 'batch_size', 'learning_rate', 
                 'results', 'error_message']
        read_only_fields = ['created_at', 'updated_at', 'status', 'results', 'error_message']
    
    def get_annotations_count(self, obj):
        """Récupère le nombre d'annotations utilisées pour l'entraînement"""
        return obj.annotations.count()