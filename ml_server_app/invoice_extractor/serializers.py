from rest_framework import serializers
from .models import Invoice

class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Invoice"""
    
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('upload_date', 'status', 'processing_time', 'extracted_data', 
                           'confidence_score', 'invoice_number', 'invoice_date', 'due_date',
                           'total_amount', 'tax_amount', 'vendor_name')

class InvoiceUploadSerializer(serializers.ModelSerializer):
    """Serializer pour l'upload de factures"""
    
    class Meta:
        model = Invoice
        fields = ('original_file',)

class InvoiceResultSerializer(serializers.ModelSerializer):
    """Serializer pour les résultats d'extraction"""
    
    class Meta:
        model = Invoice
        fields = ('id', 'status', 'extracted_data', 'confidence_score', 'invoice_number',
                 'invoice_date', 'due_date', 'total_amount', 'tax_amount', 'vendor_name')