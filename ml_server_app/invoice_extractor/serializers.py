from rest_framework import serializers
from .models import Invoice, InvoiceTemplate, InvoiceLineItem, TrainingData

class InvoiceLineItemSerializer(serializers.ModelSerializer):
    """Serializer pour les lignes de facture"""
    class Meta:
        model = InvoiceLineItem
        fields = ['id', 'description', 'quantity', 'unit_price', 'total_price']

class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer pour les factures"""
    line_items = InvoiceLineItemSerializer(many=True, read_only=True)
    file = serializers.FileField(write_only=True, required=False)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'file', 'original_filename', 'uploaded_at', 'processed_at', 
            'status', 'error_message', 'vendor_name', 'invoice_number', 
            'invoice_date', 'due_date', 'total_amount', 'tax_amount', 
            'currency', 'extracted_data', 'template', 'line_items'
        ]
        read_only_fields = [
            'id', 'original_filename', 'uploaded_at', 'processed_at', 
            'status', 'error_message', 'vendor_name', 'invoice_number', 
            'invoice_date', 'due_date', 'total_amount', 'tax_amount', 
            'currency', 'extracted_data'
        ]

class InvoiceTemplateSerializer(serializers.ModelSerializer):
    """Serializer pour les templates de factures"""
    class Meta:
        model = InvoiceTemplate
        fields = [
            'id', 'name', 'description', 'vendor', 'created_at', 'updated_at',
            'amount_regex', 'date_regex', 'invoice_number_regex', 'tax_regex'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class TrainingDataSerializer(serializers.ModelSerializer):
    """Serializer pour les données d'entraînement"""
    class Meta:
        model = TrainingData
        fields = [
            'id', 'file', 'original_filename', 'uploaded_at', 
            'annotations', 'dataset_type', 'is_validated'
        ]
        read_only_fields = ['id', 'original_filename', 'uploaded_at']