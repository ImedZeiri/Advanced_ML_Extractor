from rest_framework import serializers
from .models import Invoice

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'file', 'uploaded_at', 'processed']
        read_only_fields = ['uploaded_at', 'processed']