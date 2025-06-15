from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from django.conf import settings
import os

from .models import Invoice
from .serializers import InvoiceSerializer
from .extractors import TextExtractor

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            invoice = serializer.save()
            
            # Extraire le texte de la facture
            file_path = os.path.join(settings.MEDIA_ROOT, invoice.file.name)
            extracted_data = TextExtractor.extract_from_file(file_path)
            
            # Enregistrer le texte extrait
            invoice.set_extracted_text(extracted_data)
            
            # Retourner la réponse avec les données extraites
            return Response({
                'status': 'success',
                'message': 'Facture téléchargée et traitée avec succès',
                'invoice': self.get_serializer(invoice).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def extract(self, request, pk=None):
        """
        Endpoint pour extraire à nouveau le texte d'une facture existante
        """
        invoice = self.get_object()
        file_path = os.path.join(settings.MEDIA_ROOT, invoice.file.name)
        
        if not os.path.exists(file_path):
            return Response({
                'status': 'error',
                'message': 'Fichier non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        
        extracted_data = TextExtractor.extract_from_file(file_path)
        invoice.set_extracted_text(extracted_data)
        
        return Response({
            'status': 'success',
            'message': 'Texte extrait avec succès',
            'invoice': self.get_serializer(invoice).data
        })