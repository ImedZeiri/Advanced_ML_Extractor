from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from .models import Invoice
from .serializers import InvoiceSerializer, InvoiceUploadSerializer, InvoiceResultSerializer

class InvoiceViewSet(viewsets.ModelViewSet):
    """
    API pour l'extraction d'informations à partir de factures
    """
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]  # Autoriser l'accès sans authentification
    
    def get_serializer_class(self):
        """Sélectionne le serializer approprié selon l'action"""
        if self.action == 'create' or self.action == 'upload':
            return InvoiceUploadSerializer
        elif self.action == 'results':
            return InvoiceResultSerializer
        return self.serializer_class
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Point d'entrée pour l'upload de factures
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            invoice = serializer.save()
            return Response({
                'id': invoice.id,
                'status': invoice.status,
                'message': 'Facture téléchargée avec succès. Traitement en cours.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """
        Récupère les résultats d'extraction pour une facture spécifique
        """
        invoice = get_object_or_404(Invoice, pk=pk)
        serializer = self.get_serializer(invoice)
        return Response(serializer.data)