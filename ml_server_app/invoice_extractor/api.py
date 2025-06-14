from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import uuid
import json
import logging

from .models import Invoice, InvoiceTemplate, TrainingData
from .pipeline import InvoiceExtractionPipeline
from .serializers import InvoiceSerializer, InvoiceTemplateSerializer, TrainingDataSerializer

# Configuration du logger
logger = logging.getLogger(__name__)

class InvoiceViewSet(viewsets.ModelViewSet):
    """API endpoint pour les factures"""
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]  # Permettre l'accès sans authentification
    
    def create(self, request, *args, **kwargs):
        """
        Endpoint pour uploader et traiter une facture
        """
        try:
            # Récupération du fichier
            file = request.FILES.get('file')
            if not file:
                return Response({'error': 'Aucun fichier fourni'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérification de l'extension
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                return Response({'error': 'Format de fichier non pris en charge'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Création de l'objet Invoice
            invoice = Invoice(
                file=file,
                original_filename=file.name,
                status='pending'
            )
            invoice.save()
            
            # Traitement asynchrone (dans un cas réel, on utiliserait Celery)
            # Pour cet exemple, on traite directement
            self._process_invoice(invoice.id)
            
            # Retour de la réponse
            serializer = self.get_serializer(invoice)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la facture: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _process_invoice(self, invoice_id):
        """
        Traite une facture
        
        Args:
            invoice_id: ID de la facture à traiter
        """
        try:
            # Récupération de la facture
            invoice = Invoice.objects.get(id=invoice_id)
            
            # Mise à jour du statut
            invoice.mark_as_processing()
            
            # Initialisation du pipeline
            pipeline = InvoiceExtractionPipeline()
            
            # Traitement de la facture
            results = pipeline.process_invoice(invoice.file.path)
            
            # Mise à jour de la facture avec les résultats
            invoice.mark_as_completed(results)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la facture {invoice_id}: {str(e)}")
            
            # Récupération de la facture
            try:
                invoice = Invoice.objects.get(id=invoice_id)
                invoice.mark_as_error(str(e))
            except:
                pass
    
    @action(detail=False, methods=['post'])
    def batch_process(self, request):
        """
        Endpoint pour traiter un lot de factures
        """
        try:
            # Récupération des fichiers
            files = request.FILES.getlist('files')
            if not files:
                return Response({'error': 'Aucun fichier fourni'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Traitement de chaque fichier
            invoices = []
            for file in files:
                # Vérification de l'extension
                ext = os.path.splitext(file.name)[1].lower()
                if ext not in ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                    continue
                
                # Création de l'objet Invoice
                invoice = Invoice(
                    file=file,
                    original_filename=file.name,
                    status='pending'
                )
                invoice.save()
                invoices.append(invoice)
                
                # Traitement asynchrone (dans un cas réel, on utiliserait Celery)
                # Pour cet exemple, on traite directement
                self._process_invoice(invoice.id)
            
            # Retour de la réponse
            serializer = self.get_serializer(invoices, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Erreur lors du traitement du lot de factures: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InvoiceTemplateViewSet(viewsets.ModelViewSet):
    """API endpoint pour les templates de factures"""
    queryset = InvoiceTemplate.objects.all()
    serializer_class = InvoiceTemplateSerializer
    permission_classes = [AllowAny]  # Permettre l'accès sans authentification

class TrainingDataViewSet(viewsets.ModelViewSet):
    """API endpoint pour les données d'entraînement"""
    queryset = TrainingData.objects.all()
    serializer_class = TrainingDataSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]  # Permettre l'accès sans authentification
    
    @action(detail=False, methods=['post'])
    def import_dataset(self, request):
        """
        Endpoint pour importer un dataset
        """
        try:
            # Récupération du type de dataset
            dataset_type = request.data.get('dataset_type')
            if not dataset_type or dataset_type not in ['funsd', 'invoice2data']:
                return Response({'error': 'Type de dataset non valide'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialisation du pipeline
            pipeline = InvoiceExtractionPipeline()
            
            # Chargement des données
            training_data = pipeline.load_training_data(dataset_type)
            
            # Importation des données
            imported_count = 0
            for data in training_data:
                # Copie du fichier
                file_path = data['image_path']
                file_name = os.path.basename(file_path)
                
                # Lecture du fichier
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # Sauvegarde du fichier
                path = default_storage.save(f'training_data/{file_name}', ContentFile(file_content))
                
                # Création de l'objet TrainingData
                training_data_obj = TrainingData(
                    file=path,
                    original_filename=file_name,
                    annotations=data['annotation'],
                    dataset_type=dataset_type,
                    is_validated=True
                )
                training_data_obj.save()
                imported_count += 1
            
            return Response({'message': f'{imported_count} fichiers importés avec succès'}, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Erreur lors de l'importation du dataset: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def train_model(self, request):
        """
        Endpoint pour entraîner un modèle
        """
        try:
            # Récupération des paramètres
            dataset_type = request.data.get('dataset_type', 'funsd')
            model_name = request.data.get('model_name', 'invoice_extractor')
            
            # Initialisation du pipeline
            pipeline = InvoiceExtractionPipeline()
            
            # Chargement des données
            training_data = pipeline.load_training_data(dataset_type)
            
            # Entraînement du modèle
            model_path = pipeline.train_model(training_data, model_name)
            
            return Response({
                'message': f'Modèle entraîné avec succès',
                'model_path': model_path,
                'training_samples': len(training_data)
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement du modèle: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)